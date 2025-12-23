import asyncio
import random
import toml
from enum import Enum, auto
from telethon import TelegramClient, events
from src.logger import logger
from src.parser import parse_message
from src.models import MessageType, strings, ActionMode
from src.shop import ShopManager
from src.interactor import Interactor
from src.utils import get_message_text, human_delay

class BotState(Enum):
    ACTIVE = auto()
    SLEEPY = auto()
    RESTING = auto()

class KomaruBot:
    def __init__(self):
        self.config = toml.load("config.toml")
        self.app = TelegramClient("my_account", self.config["api_id"], self.config["api_hash"])
        
        self.interactor = Interactor(self.app, self.config)
        self.shop = ShopManager(self.interactor)

        self.target_bot_id = self.config["target_bot_id"]
        self.game_settings = self.config["game_settings"]
        self.behavior_settings = self.config["behavior"]
        self.mode = self.config.get("mode", "automatic")

        self.current_coins = 0
        self.luck_booster_active = False
        self.is_busy = False
        
        self.state = BotState.ACTIVE
        self.actions_since_rest = 0
        self.current_cooldown_duration = 0
        self.cooldown_task = None

    async def start(self):
        await self.app.start()
        await self.update_balance_from_profile()

        logger.info(strings.LOG_ANALYZING_STATE)

        if self.mode == "semi-automatic":
            await self.app.send_message(self.target_bot_id, strings.CMD_KOMARU)
            await self._main_loop(initial_state=None)
        else:
            async for last_msg in self.app.iter_messages(self.target_bot_id, limit=1):
                message_text = get_message_text(last_msg)
                if not message_text:
                    logger.info(strings.LOG_INITIAL_STATE_CLEAR)
                    await self._main_loop(initial_state=None)
                    break

                parsed_initial = parse_message(message_text)
                if parsed_initial.type == MessageType.COOLDOWN:
                    logger.info(strings.LOG_INITIAL_STATE_COOLDOWN)
                    await self._main_loop(initial_state=parsed_initial)
                else:
                    logger.info(strings.LOG_INITIAL_STATE_CLEAR)
                    await self._main_loop(initial_state=None)
                break

        await self.app.run_until_disconnected()

    async def update_balance_from_profile(self):
        logger.info(strings.LOG_UPDATING_BALANCE)
        self.is_busy = True
        try:
            msg = await self.interactor.execute_action(ActionMode.SEND, message=strings.CMD_PROFILE)
            message_text = get_message_text(msg)
            if not message_text:
                logger.warning(strings.LOG_PROFILE_NO_TEXT)
            else:
                parsed = parse_message(message_text)
                if parsed.type == MessageType.PROFILE_INFO:
                    self.current_coins = parsed.details["total_coins"]
                    logger.success(strings.LOG_BALANCE_UPDATED.format(coins=self.current_coins))
                    await human_delay(1, 3)
                else:
                    logger.warning(strings.LOG_UNEXPECTED_PROFILE_RESPONSE.format(text=message_text[:100]))
        except TimeoutError:
            logger.error(strings.LOG_PROFILE_TIMEOUT)
        except Exception as e:
            logger.error(strings.LOG_PROFILE_UPDATE_ERROR.format(e=e))
        finally:
            self.is_busy = False

    async def _handle_card_reception(self, parsed_data):
        if self.cooldown_task and not self.cooldown_task.done():
            self.cooldown_task.cancel()

        self.current_coins = parsed_data.details["total_coins"]
        logger.success(strings.LOG_GOT_CARD.format(name=parsed_data.details['name'], coins=self.current_coins))
        if parsed_data.details.get("booster_used"): self.luck_booster_active = False
        await self._decide_and_act()

    async def _handle_cooldown(self, parsed_data):
        if self.cooldown_task and not self.cooldown_task.done():
            self.cooldown_task.cancel()
            logger.debug(strings.LOG_COOLDOWN_TASK_CANCELLED_EXISTING)

        cooldown = parsed_data.details['cooldown']
        self.current_cooldown_duration = cooldown
        h, m, s = cooldown // 3600, (cooldown % 3600) // 60, cooldown % 60
        logger.warning(strings.LOG_COOLDOWN.format(h=h, m=m, s=s))

        if self.mode == "automatic":
            use_chance = self.behavior_settings["use_time_booster_chance"]
            if cooldown > 3600 and random.random() < use_chance:
                self.is_busy = True
                logger.info(strings.LOG_COOLDOWN_USE_BOOSTER)
                booster_name = strings.BOOSTER_TIME
                booster_count, booster_msg = await self.shop.get_booster_count(booster_name)
                if booster_count > 0:
                    await self.shop.use_booster(booster_name)
                elif self.current_coins >= self.game_settings["time_booster_cost"]:
                    if await self.shop.buy_booster(booster_name):
                        await self.update_balance_from_profile()
                        _, new_booster_msg = await self.shop.get_booster_count(booster_name)
                        if new_booster_msg:
                            await self.shop.use_booster(booster_name)
                else:
                    if booster_msg:
                        await self.shop.navigate_back(booster_msg)

                self.is_busy = False
                logger.info(strings.LOG_CHECKING_NEW_COOLDOWN)
                await human_delay(3, 7)
                await self.app.send_message(self.target_bot_id, strings.CMD_KOMARU)
            else:
                if cooldown > 3600: logger.info(strings.LOG_COOLDOWN_WAIT)
                logger.info(strings.LOG_WAITING_SECS.format(seconds=cooldown))
                self.cooldown_task = asyncio.create_task(asyncio.sleep(cooldown + random.uniform(10, 60)))
                await self.cooldown_task
                await self._decide_and_act()
        else: # semi-automatic mode
            logger.info(strings.LOG_WAITING_SECS.format(seconds=cooldown))
            self.cooldown_task = asyncio.create_task(asyncio.sleep(cooldown + random.uniform(10, 60)))
            await self.cooldown_task
            await self._decide_and_act()


    async def _decide_and_act(self):
        self.is_busy = True
        self.actions_since_rest += 1

        if self.actions_since_rest > self.behavior_settings["max_actions_before_rest"]:
            self.state = BotState.SLEEPY
            if random.random() < self.behavior_settings["rest_chance"]:
                self.state = BotState.RESTING
                rest_min = self.behavior_settings["rest_duration_min_minutes"]
                rest_max = self.behavior_settings["rest_duration_max_minutes"]
                rest_duration = random.uniform(rest_min * 60, rest_max * 60)
                logger.info(strings.LOG_BOT_TIRED.format(minutes=rest_duration / 60))
                
                await asyncio.sleep(rest_duration)
                
                logger.info(strings.LOG_BOT_WAKING_UP)
                await self.update_balance_from_profile()
                self.actions_since_rest = 0
                self.state = BotState.ACTIVE

        if random.random() < self.behavior_settings["spontaneous_profile_check_chance"]:
            await self.update_balance_from_profile()

        if self.mode == "automatic": # only check/use luck booster in automatic mode
            min_coins_for_luck = self.game_settings["luck_booster_min_coins_threshold"]
            if not self.luck_booster_active and self.current_coins > min_coins_for_luck:
                booster_name = strings.BOOSTER_LUCK
                booster_count, booster_msg = await self.shop.get_booster_count(booster_name)
                if booster_count > 0:
                    if await self.shop.use_booster(booster_name): 
                        self.luck_booster_active = True
                elif self.current_coins >= self.game_settings["luck_booster_cost"] + min_coins_for_luck:
                    if await self.shop.buy_booster(booster_name):
                        await self.update_balance_from_profile()
                        _, new_booster_msg = await self.shop.get_booster_count(booster_name)
                        if new_booster_msg:
                            if await self.shop.use_booster(booster_name): 
                                self.luck_booster_active = True
                else:
                    if booster_msg:
                        await self.shop.navigate_back(booster_msg)


        self.is_busy = False
        await human_delay(10, 45)
        logger.info(strings.LOG_SENDING_CARD_MESSAGE)
        await self.app.send_message(self.target_bot_id, strings.CMD_KOMARU)

    async def _main_loop(self, initial_state=None):
        @self.app.on(events.NewMessage(from_users=self.target_bot_id))
        async def message_handler(event):
            message = event.message
            message_text = get_message_text(message)
            if not message_text:
                logger.debug(strings.LOG_EMPTY_MESSAGE_IGNORED)
                return

            parsed = parse_message(message_text)
            if parsed.type in [MessageType.NEW_CARD, MessageType.DUPLICATE_CARD]:
                await self._handle_card_reception(parsed)
            elif parsed.type == MessageType.COOLDOWN:
                await self._handle_cooldown(parsed)

        @self.app.on(events.MessageEdited(from_users=self.target_bot_id))
        async def message_edited_handler(event):
            message = event.message
            message_text = get_message_text(message)
            if not message_text:
                logger.debug(strings.LOG_EMPTY_EDITED_MESSAGE_IGNORED)
                return

            parsed = parse_message(message_text)
            if parsed.type == MessageType.COOLDOWN_REDUCED and self.mode == "semi-automatic":
                if self.cooldown_task and not self.cooldown_task.done():
                    self.cooldown_task.cancel()
                    logger.debug(strings.LOG_COOLDOWN_TASK_CANCELLED_REDUCTION)

                self.current_cooldown_duration = max(0, self.current_cooldown_duration - 3600)
                h, m, s = self.current_cooldown_duration // 3600, (self.current_cooldown_duration % 3600) // 60, self.current_cooldown_duration % 60
                logger.info(strings.LOG_COOLDOWN_NEW_DURATION.format(h=h, m=m, s=s))

                if self.current_cooldown_duration <= 0:
                    logger.info(strings.LOG_COOLDOWN_CLEARED_SENDING_CMD)
                    await self._decide_and_act()
                else:
                    logger.info(strings.LOG_WAITING_SECS.format(seconds=self.current_cooldown_duration))
                    self.cooldown_task = asyncio.create_task(asyncio.sleep(self.current_cooldown_duration + random.uniform(10, 60)))
                    await self.cooldown_task
                    await self._decide_and_act()

        logger.info(strings.LOG_MAIN_LOOP_RUNNING)
        if initial_state:
            await self._handle_cooldown(initial_state)
        else:
            if self.mode == "automatic":
                await self._decide_and_act()
        await asyncio.Event().wait()
