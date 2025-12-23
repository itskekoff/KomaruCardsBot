import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from .models import strings, ActionMode
from .logger import logger
from .utils import human_delay

ASYNCIO_TIMEOUT = 5


class Interactor:
    def __init__(self, app: TelegramClient, config: dict):
        self.app = app
        self.target_bot_id = config["target_bot_id"]
        self.new_message_queue = asyncio.Queue()
        self.edited_message_queues = {}

        self.app.add_event_handler(self._on_new_message, events.NewMessage(chats=self.target_bot_id))
        self.app.add_event_handler(self._on_message_edited, events.MessageEdited(chats=self.target_bot_id))

    async def _on_new_message(self, event):
        logger.debug(
            strings.LOG_INTERACTOR_NEW_MESSAGE_EVENT.format(message_id=event.message.id, chat_id=event.chat_id))
        await self.new_message_queue.put(event.message)

    async def _on_message_edited(self, event):
        if event.message.id in self.edited_message_queues:
            logger.debug(
                strings.LOG_INTERACTOR_EDITED_MESSAGE_EVENT.format(
                    message_id=event.message.id,
                    chat_id=event.chat_id,
                    monitored_ids=list(self.edited_message_queues.keys())
                ))
            logger.debug(strings.LOG_INTERACTOR_PUTTING_EDITED_MESSAGE.format(message_id=event.message.id))
            await self.edited_message_queues[event.message.id].put(event.message)

    def _clear_new_message_queue(self):
        while not self.new_message_queue.empty():
            self.new_message_queue.get_nowait()

    async def _wait_for_new_message(self, timeout: float | None = ASYNCIO_TIMEOUT) -> Message:
        try:
            coro = self.new_message_queue.get()
            if timeout is not None:
                msg = await asyncio.wait_for(coro, timeout=timeout)
            else:
                msg = await coro

            logger.debug(strings.LOG_INTERACTOR_GOT_NEW_MESSAGE.format(message_id=msg.id))
            return msg
        except asyncio.TimeoutError:
            logger.warning(strings.LOG_INTERACTOR_TIMEOUT_NEW_MESSAGE)
            raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)

    async def _wait_for_message_edit(self, message_id, timeout: float | None = ASYNCIO_TIMEOUT) -> Message:
        edit_queue = asyncio.Queue(1)
        self.edited_message_queues[message_id] = edit_queue
        try:
            coro = edit_queue.get()
            if timeout is not None:
                msg = await asyncio.wait_for(coro, timeout=timeout)
            else:
                msg = await coro

            logger.debug(strings.LOG_INTERACTOR_GOT_EDITED_MESSAGE.format(message_id=msg.id))
            return msg
        except asyncio.TimeoutError:
            logger.warning(strings.LOG_INTERACTOR_TIMEOUT_MESSAGE_EDIT.format(message_id=message_id))
            raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)
        finally:
            self.edited_message_queues.pop(message_id, None)

    async def execute_action(self, action: ActionMode, message: str = None, button_text: str = None,
                             original_message: Message = None) -> Message | None:
        await human_delay()

        self._clear_new_message_queue()
        if action == ActionMode.SEND:
            logger.debug(strings.LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_SEND)
        elif action == ActionMode.CLICK:
            logger.debug(strings.LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_CLICK)

        if action == ActionMode.SEND:
            logger.debug(
                strings.LOG_INTERACTOR_SENDING_MESSAGE.format(target_bot_id=self.target_bot_id, message=message))
            await self.app.send_message(self.target_bot_id, message)
            return await self._wait_for_new_message(timeout=ASYNCIO_TIMEOUT)

        elif action == ActionMode.CLICK:
            if not original_message or not original_message.buttons:
                raise ValueError(strings.ERROR_NO_REPLY_MARKUP)

            logger.debug(
                strings.LOG_INTERACTOR_ATTEMPTING_CLICK.format(button_text=button_text, message_id=original_message.id))

            task_new = asyncio.create_task(self._wait_for_new_message(timeout=None))
            task_edit = asyncio.create_task(self._wait_for_message_edit(original_message.id, timeout=None))
            response_tasks = {task_new, task_edit}

            task_click = asyncio.create_task(original_message.click(text=button_text))

            logger.debug(strings.LOG_INTERACTOR_CREATED_WAITERS.format(message_id=original_message.id))
            logger.debug(strings.LOG_INTERACTOR_AWAITING_CLICK.format(button_text=button_text))

            all_tasks = response_tasks | {task_click}
            click_successful = False

            try:
                while True:
                    done, pending = await asyncio.wait(all_tasks, return_when=asyncio.FIRST_COMPLETED,
                                                       timeout=ASYNCIO_TIMEOUT)

                    if not done:
                        if click_successful:
                            for t in all_tasks: t.cancel()
                            await asyncio.gather(*all_tasks, return_exceptions=True)
                            return original_message

                        raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)

                    for task in done:
                        if task == task_click:
                            try:
                                await task
                                logger.debug(strings.LOG_INTERACTOR_CLICK_SENT_SUCCESS.format(button_text=button_text))
                                click_successful = True
                                all_tasks.remove(task_click)
                            except Exception as e:
                                logger.error(strings.LOG_INTERACTOR_CLICK_FAILED.format(e=e))
                                if "Could not find any button" in str(e):
                                    raise ValueError(strings.ERROR_BUTTON_NOT_FOUND.format(name=button_text))
                                raise e

                        elif task in response_tasks:
                            result_msg = task.result()
                            logger.success(strings.LOG_INTERACTOR_SUCCESS_RESPONSE.format(message_id=result_msg.id))

                            for t in (pending | done):
                                if not t.done(): t.cancel()

                            if pending:
                                await asyncio.gather(*pending, return_exceptions=True)

                            return result_msg

            except Exception as e:
                for t in all_tasks:
                    t.cancel()
                await asyncio.gather(*all_tasks, return_exceptions=True)

                if isinstance(e, asyncio.TimeoutError) and click_successful:
                    return original_message

                if isinstance(e, asyncio.TimeoutError):
                    logger.warning(strings.LOG_INTERACTOR_TIMEOUT_CLICK_RESPONSE.format(button_text=button_text))
                raise e

        return None
