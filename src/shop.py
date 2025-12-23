import re
from functools import wraps

from telethon.tl.custom import Message
from telethon.tl.custom.message import Message
from .logger import logger
from .models import strings, ActionMode
from .interactor import Interactor
from .utils import get_message_text, remove_formatting


def shop_action(error_log_string: str, default_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            history = []
            kwargs.setdefault('history', history)
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.error(error_log_string.format(e=e))
                if history:
                    await self.navigate_back(history[-1])
                return default_return

        return wrapper

    return decorator


class ShopManager:
    def __init__(self, interactor: Interactor):
        self.interactor = interactor

    async def navigate_back(self, current_message: Message, steps: int = 3):
        msg = current_message
        for i in range(steps):
            try:
                message_text = get_message_text(msg)
                if not msg or not msg.buttons or not message_text or strings.BTN_BACK not in message_text:
                    break
                logger.debug(strings.LOG_NAVIGATION_BACK.format(current=i + 1, total=steps))
                msg = await self.interactor.execute_action(ActionMode.CLICK, original_message=msg,
                                                           button_text=strings.BTN_BACK)
            except (ValueError, TimeoutError):
                break

    async def _navigate(self, history: list, steps: list[tuple[ActionMode, str]]) -> Message:
        msg = None
        for i, (action, text) in enumerate(steps):
            if action == ActionMode.SEND:
                msg = await self.interactor.execute_action(ActionMode.SEND, message=text)
            elif action == ActionMode.CLICK:
                if msg is None:
                    raise ValueError()
                msg = await self.interactor.execute_action(ActionMode.CLICK, original_message=msg, button_text=text)
            else:
                raise ValueError()

            history.append(msg)
        return msg

    async def _navigate_to_inventory_boosters(self, history: list) -> Message:
        return await self._navigate(history, [
            (ActionMode.SEND, strings.CMD_PROFILE),
            (ActionMode.CLICK, strings.BTN_INVENTORY),
            (ActionMode.CLICK, strings.BTN_BOOSTERS)
        ])

    async def _navigate_to_shop_boosters(self, history: list) -> Message:
        return await self._navigate(history, [
            (ActionMode.SEND, strings.CMD_SHOP),
            (ActionMode.CLICK, strings.BTN_BOOSTERS)
        ])

    async def _perform_booster_action(
            self, history: list, booster_name: str, navigation_func,
            action_button: str, success_keyword: str,
            success_log: str, failure_log: str
    ) -> bool:
        msg = await navigation_func(history)

        button_to_click = None
        if msg and msg.buttons:
            for row in msg.buttons:
                for button in row:
                    if button.text.startswith(booster_name):
                        button_to_click = button.text
                        break
                if button_to_click:
                    break

        if not button_to_click:
            logger.error(failure_log.format(name=booster_name))
            if msg:
                await self.navigate_back(msg)
            return False

        msg = await self.interactor.execute_action(ActionMode.CLICK, original_message=msg, button_text=button_to_click)
        history.append(msg)

        logger.debug(strings.LOG_SHOP_MESSAGE_CONTENT_BEFORE_CLICK.format(action_button=action_button, message_text=get_message_text(msg)))
        final_msg = await self.interactor.execute_action(ActionMode.CLICK, original_message=msg,
                                                         button_text=action_button)
        history.append(final_msg)

        message_text = get_message_text(final_msg)
        if message_text and success_keyword in message_text:
            logger.success(success_log.format(name=booster_name))
            await self.navigate_back(final_msg)
            return True
        else:
            logger.error(failure_log.format(name=booster_name))
            await self.navigate_back(final_msg)
            return False

    @shop_action(strings.LOG_SHOP_ERROR_CHECKING_INVENTORY, default_return=0)
    async def get_booster_count(self, booster_name: str, **kwargs) -> int | tuple[int, Message]:
        history = kwargs['history']
        logger.info(strings.LOG_SHOP_CHECKING_BOOSTER.format(name=booster_name))
        boosters_menu_msg = await self._navigate_to_inventory_boosters(history)
        if boosters_menu_msg and boosters_menu_msg.buttons:
            button_to_click = None
            for row in boosters_menu_msg.buttons:
                for button in row:
                    if button.text.startswith(booster_name):
                        button_to_click = button.text
                        break
                if button_to_click:
                    break

            if not button_to_click:
                logger.info(strings.LOG_SHOP_BOOSTER_NOT_FOUND.format(name=booster_name))
                if boosters_menu_msg:
                    await self.navigate_back(boosters_menu_msg)
                return 0

            result = await self.interactor.execute_action(action=ActionMode.CLICK, original_message=boosters_menu_msg,
                                                          button_text=button_to_click)
            if result and result.buttons:
                result_text = remove_formatting(result.text)
                match = re.search(r"\[(\d+) шт]", result_text)
                if match:
                    count = int(match.group(1))
                    logger.info(strings.LOG_SHOP_FOUND_BOOSTERS.format(name=booster_name, count=count))
                    await self.navigate_back(result)
                    return count, result

        logger.info(strings.LOG_SHOP_BOOSTER_NOT_FOUND.format(name=booster_name))
        if boosters_menu_msg:
            await self.navigate_back(boosters_menu_msg)
        return 0

    @shop_action(strings.LOG_SHOP_ERROR_BUYING, default_return=False)
    async def buy_booster(self, booster_name: str, **kwargs) -> bool:
        history = kwargs['history']
        logger.info(strings.LOG_SHOP_BUYING_BOOSTER.format(name=booster_name))
        return await self._perform_booster_action(
            history=history,
            booster_name=booster_name,
            navigation_func=self._navigate_to_shop_boosters,
            action_button=strings.BTN_BUY,
            success_keyword=strings.KEYWORD_BOUGHT,
            success_log=strings.LOG_SHOP_BOUGHT_SUCCESS,
            failure_log=strings.LOG_SHOP_CANT_BUY
        )

    @shop_action(strings.LOG_SHOP_ERROR_ACTIVATING, default_return=False)
    async def use_booster(self, booster_name: str, **kwargs) -> bool:
        history = kwargs['history']
        logger.info(strings.LOG_SHOP_ACTIVATING_BOOSTER.format(name=booster_name))
        return await self._perform_booster_action(
            history=history,
            booster_name=booster_name,
            navigation_func=self._navigate_to_inventory_boosters,
            action_button=strings.BTN_ACTIVATE,
            success_keyword=strings.KEYWORD_ACTIVATED,
            success_log=strings.LOG_SHOP_ACTIVATED_SUCCESS,
            failure_log=strings.LOG_SHOP_CANT_ACTIVATE
        )
