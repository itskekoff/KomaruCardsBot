import asyncio
import random
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message
from .models import strings, ActionMode
from .logger import logger

class Interactor:
    def __init__(self, app: TelegramClient, config: dict):
        self.app = app
        self.target_bot_id = config["target_bot_id"]
        self.new_message_queue = asyncio.Queue()
        self.edited_message_queues = {}

        self.app.add_event_handler(self._on_new_message, events.NewMessage(chats=self.target_bot_id))
        self.app.add_event_handler(self._on_message_edited, events.MessageEdited(chats=self.target_bot_id))

    async def _on_new_message(self, event):
        logger.debug(strings.LOG_INTERACTOR_NEW_MESSAGE_EVENT.format(message_id=event.message.id, chat_id=event.chat_id))
        await self.new_message_queue.put(event.message)

    async def _on_message_edited(self, event):
        logger.debug(strings.LOG_INTERACTOR_EDITED_MESSAGE_EVENT.format(message_id=event.message.id, chat_id=event.chat_id, monitored_ids=list(self.edited_message_queues.keys())))
        if event.message.id in self.edited_message_queues:
            logger.debug(strings.LOG_INTERACTOR_PUTTING_EDITED_MESSAGE.format(message_id=event.message.id))
            await self.edited_message_queues[event.message.id].put(event.message)

    @staticmethod
    async def _human_delay(min_sec=0.5, max_sec=1.0):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def _wait_for_new_message(self, timeout=15) -> Message:
        try:
            logger.debug(strings.LOG_INTERACTOR_WAITING_NEW_MESSAGE.format(timeout=timeout))
            msg = await asyncio.wait_for(self.new_message_queue.get(), timeout=timeout)
            logger.debug(strings.LOG_INTERACTOR_GOT_NEW_MESSAGE.format(message_id=msg.id))
            return msg
        except asyncio.TimeoutError:
            logger.warning(strings.LOG_INTERACTOR_TIMEOUT_NEW_MESSAGE)
            raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)

    async def _wait_for_message_edit(self, message_id, timeout=15) -> Message:
        edit_queue = asyncio.Queue(1)
        self.edited_message_queues[message_id] = edit_queue
        try:
            logger.debug(strings.LOG_INTERACTOR_WAITING_MESSAGE_EDIT.format(message_id=message_id, timeout=timeout))
            msg = await asyncio.wait_for(edit_queue.get(), timeout=timeout)
            logger.debug(strings.LOG_INTERACTOR_GOT_EDITED_MESSAGE.format(message_id=msg.id))
            return msg
        except asyncio.TimeoutError:
            logger.warning(strings.LOG_INTERACTOR_TIMEOUT_MESSAGE_EDIT.format(message_id=message_id))
            raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)
        finally:
            if message_id in self.edited_message_queues:
                del self.edited_message_queues[message_id]

    async def execute_action(self, action: ActionMode, message: str = None, button_text: str = None, original_message: Message = None) -> Message | None:
        if action == ActionMode.SEND:
            logger.debug(strings.LOG_INTERACTOR_SENDING_MESSAGE.format(target_bot_id=self.target_bot_id, message=message))
            while not self.new_message_queue.empty():
                self.new_message_queue.get_nowait()
            logger.debug(strings.LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_SEND)
            await self.app.send_message(self.target_bot_id, message)
            return await self._wait_for_new_message()

        elif action == ActionMode.CLICK:
            logger.debug(strings.LOG_INTERACTOR_ATTEMPTING_CLICK.format(button_text=button_text, message_id=original_message.id))
            if not original_message or not original_message.buttons:
                raise ValueError(strings.ERROR_NO_REPLY_MARKUP)

            while not self.new_message_queue.empty():
                self.new_message_queue.get_nowait()
            logger.debug(strings.LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_CLICK)
            
            new_message_waiter = asyncio.create_task(self._wait_for_new_message())
            edit_waiter = asyncio.create_task(self._wait_for_message_edit(original_message.id))
            waiters = {new_message_waiter, edit_waiter}
            logger.debug(strings.LOG_INTERACTOR_CREATED_WAITERS.format(message_id=original_message.id))

            try:
                logger.debug(strings.LOG_INTERACTOR_AWAITING_CLICK.format(button_text=button_text))
                await original_message.click(text=button_text)
                logger.debug(strings.LOG_INTERACTOR_CLICK_SENT_SUCCESS.format(button_text=button_text))
            except Exception as e:
                logger.error(strings.LOG_INTERACTOR_CLICK_FAILED.format(e=e))
                for task in waiters:
                    task.cancel()
                raise

            try:
                logger.debug(strings.LOG_INTERACTOR_WAITING_RESPONSE)
                done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)
                logger.debug(strings.LOG_INTERACTOR_ASYNCIO_WAIT_COMPLETED.format(done_tasks=len(done), pending_tasks=len(pending)))

                for task in pending:
                    task.cancel()
                    logger.debug(strings.LOG_INTERACTOR_CANCELLED_PENDING_TASK.format(task_id=id(task)))

                if not done:
                    logger.warning(strings.LOG_INTERACTOR_TIMEOUT_CLICK_RESPONSE.format(button_text=button_text))
                    raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)

                result_message = await done.pop()
                logger.success(strings.LOG_INTERACTOR_SUCCESS_RESPONSE.format(message_id=result_message.id))
                return result_message

            except Exception as e:
                logger.error(strings.LOG_INTERACTOR_EXCEPTION_WAITING_RESPONSE.format(e=e))
                if "Could not find any button with text" in str(e):
                     raise ValueError(strings.ERROR_BUTTON_NOT_FOUND.format(name=button_text))
                if isinstance(e, asyncio.TimeoutError):
                    raise TimeoutError(strings.ERROR_ANSWER_TIMEOUT)
                raise

        return None
