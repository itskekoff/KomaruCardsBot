from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, List

class MessageType(Enum):
    NEW_CARD = auto()
    DUPLICATE_CARD = auto()
    COOLDOWN = auto()
    COOLDOWN_REDUCED = auto()
    PROFILE_INFO = auto()
    UNKNOWN = auto()

class ActionMode(Enum):
    SEND = auto()
    CLICK = auto()

@dataclass
class ParsedMessage:
    type: MessageType
    details: Optional[Dict[str, Any]] = None

@dataclass
class Strings:
    CMD_KOMARU: str = "камар"
    CMD_PROFILE: str = "/profile"
    CMD_SHOP: str = "/shop"

    KEYWORD_CARD_INTRO_VARIANTS: List[str] = field(default_factory=lambda: [
        "Вы нашли карточку",
        "Коллекция пополнилась карточкой",
        "Новая карточка —",
        "Карточка",
        "Успех! Карточка"
    ])

    KEYWORD_CARD_SUFFIX_YOURS: str = "ваша!"
    KEYWORD_CARD_SUFFIX_ALREADY_HAVE: str = "уже у вас"
    KEYWORD_CARD_SUFFIX_REPEATED: str = "у вас повторно"
    KEYWORD_CARD_SUFFIX_ALREADY_IN_COLLECTION: str = "уже в коллекции!"

    KEYWORD_RARITY_TEXT: str = "Редкость"
    KEYWORD_POINTS_TEXT: str = "Очки"
    KEYWORD_COINS_TEXT: str = "Монеты"
    KEYWORD_BOOSTER_USED_TEXT: str = "Бустер «удача»"

    KEYWORD_PROFILE_TITLE: str = "Профиль «"
    KEYWORD_COOLDOWN_VARIANTS: List[str] = field(default_factory=lambda: [
        "Подождите",
        "Попробуйте снова через",
        "Попробуйте через",
        "Возвращайтесь через"
    ])
    KEYWORD_COOLDOWN_REDUCED: str = "Бустер «ускоритель времени» активирован"
    KEYWORD_BOUGHT: str = "куплен"
    KEYWORD_ACTIVATED: str = "активирован"
    KEYWORD_INVENTORY: str = "Инвентарь"

    BTN_INVENTORY: str = "🎒 Инвентарь"
    BTN_BOOSTERS: str = "⚡️ Бустеры"
    BTN_BUY: str = "Купить"
    BTN_ACTIVATE: str = "Активировать"
    BTN_BACK: str = "‹ Назад"
    
    BOOSTER_LUCK: str = "🍀 Удача"
    BOOSTER_TIME: str = "Ускоритель времени"

    LOG_ANALYZING_STATE: str = "analyzing the initial state..."
    LOG_INITIAL_STATE_COOLDOWN: str = "initial state is cooldown. handling it..."
    LOG_INITIAL_STATE_CLEAR: str = "initial state is clear. starting normal flow..."
    LOG_UPDATING_BALANCE: str = "updating balance using profile..."
    LOG_BALANCE_UPDATED: str = "balance updated: {coins} 💰"
    LOG_PROFILE_NO_TEXT: str = "profile message has no text, can't update balance."
    LOG_UNEXPECTED_PROFILE_RESPONSE: str = "unexpected response to /profile: {text}"
    LOG_PROFILE_TIMEOUT: str = "bot did not respond to /profile command."
    LOG_PROFILE_UPDATE_ERROR: str = "an error occurred during profile update: {e}"
    LOG_EMPTY_MESSAGE_IGNORED: str = "received an empty message, ignoring."
    LOG_GOT_CARD: str = "got card: '{name}'. balance: {coins} 💰"
    LOG_COOLDOWN: str = "cooldown: {h}h {m}m {s}s"
    LOG_COOLDOWN_USE_BOOSTER: str = "cooldown >1 hour, bot decided to use time booster..."
    LOG_CHECKING_NEW_COOLDOWN: str = "checking new cooldown..."
    LOG_COOLDOWN_WAIT: str = "bot decided to not use time booster and wait."
    LOG_WAITING_SECS: str = "waiting {seconds} secs..."
    LOG_SENDING_CARD_MESSAGE: str = "sending card message"
    LOG_MAIN_LOOP_WARM_CACHE: str = "warming up cache, iterating through dialogs..."
    LOG_MAIN_LOOP_WARM_CACHE_DONE: str = "cache warmed up."
    LOG_MAIN_LOOP_RUNNING: str = "main_loop() running"
    LOG_BOT_TIRED: str = "bot is tired, resting for {minutes:.1f} minutes."
    LOG_BOT_WAKING_UP: str = "bot waking up from rest."
    
    LOG_SHOP_CHECKING_BOOSTER: str = "checking booster '{name}' in inventory..."
    LOG_SHOP_FOUND_BOOSTERS: str = "found '{name}': {count} pcs."
    LOG_SHOP_BOOSTER_NOT_FOUND: str = "booster '{name}' not found in inventory."
    LOG_SHOP_ERROR_CHECKING_INVENTORY: str = "error while checking inventory: {e}"
    LOG_SHOP_BUYING_BOOSTER: str = "trying to buy booster '{name}'..."
    LOG_SHOP_BOUGHT_SUCCESS: str = "booster '{name}' successfully bought"
    LOG_SHOP_CANT_BUY: str = "can't buy '{name}'."
    LOG_SHOP_ERROR_BUYING: str = "error while trying to buy: {e}"
    LOG_SHOP_ACTIVATING_BOOSTER: str = "trying to activate booster '{name}' from inventory..."
    LOG_SHOP_ACTIVATED_SUCCESS: str = "booster '{name}' activated."
    LOG_SHOP_CANT_ACTIVATE: str = "can't activate '{name}'."
    LOG_SHOP_ERROR_ACTIVATING: str = "error while trying activate booster: {e}"
    
    LOG_NAVIGATION_BACK: str = "navigation: step back ({current}/{total})"
    
    ERROR_NO_REPLY_MARKUP: str = "message doesn't have reply markup"
    ERROR_ANSWER_TIMEOUT: str = "answer timeout."
    ERROR_BUTTON_NOT_FOUND: str = "button '{name}' not found."

    # New logger messages for bot.py
    LOG_COOLDOWN_TASK_CANCELLED_EXISTING: str = "cancelled existing cooldown task."
    LOG_COOLDOWN_TASK_CANCELLED_REDUCTION: str = "cancelled existing cooldown task due to reduction."
    LOG_COOLDOWN_NEW_DURATION: str = "new cooldown duration: {h}h {m}m {s}s"
    LOG_COOLDOWN_CLEARED_SENDING_CMD: str = "cooldown cleared. Sending CMD_KOMARU."
    LOG_COOLDOWN_REDUCED_IGNORED_AUTO: str = "cooldown reduced message ignored in automatic mode."

    # New logger messages for interactor.py
    LOG_INTERACTOR_NEW_MESSAGE_EVENT: str = "Caught new message event: {message_id} in chat {chat_id}"
    LOG_INTERACTOR_EDITED_MESSAGE_EVENT: str = "Caught message edited event: {message_id} in chat {chat_id}. Monitored IDs: {monitored_ids}"
    LOG_INTERACTOR_PUTTING_EDITED_MESSAGE: str = "Putting edited message {message_id} into its queue."
    LOG_INTERACTOR_WAITING_NEW_MESSAGE: str = "Waiting for a new message (timeout={timeout}s)..."
    LOG_INTERACTOR_GOT_NEW_MESSAGE: str = "Got new message {message_id}"
    LOG_INTERACTOR_TIMEOUT_NEW_MESSAGE: str = "Timeout waiting for a new message."
    LOG_INTERACTOR_WAITING_MESSAGE_EDIT: str = "Waiting for message {message_id} to be edited (timeout={timeout}s)..."
    LOG_INTERACTOR_GOT_EDITED_MESSAGE: str = "Got edited message {message_id}"
    LOG_INTERACTOR_TIMEOUT_MESSAGE_EDIT: str = "Timeout waiting for message {message_id} to be edited."
    LOG_INTERACTOR_SENDING_MESSAGE: str = "Sending message to {target_bot_id}: '{message}'"
    LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_SEND: str = "Cleared new_message_queue before sending message."
    LOG_INTERACTOR_ATTEMPTING_CLICK: str = "Attempting to click button '{button_text}' on message {message_id}"
    LOG_INTERACTOR_CLEARED_NEW_MESSAGE_QUEUE_CLICK: str = "Cleared new_message_queue before click."
    LOG_INTERACTOR_CREATED_WAITERS: str = "Created waiters for message {message_id}."
    LOG_INTERACTOR_AWAITING_CLICK: str = "Awaiting click for button '{button_text}'..."
    LOG_INTERACTOR_CLICK_SENT_SUCCESS: str = "Click for button '{button_text}' sent successfully."
    LOG_INTERACTOR_CLICK_FAILED: str = "The `message.click()` call itself failed: {e}"
    LOG_INTERACTOR_WAITING_RESPONSE: str = "Now waiting for a response from the bot (new message or edit)..."
    LOG_INTERACTOR_ASYNCIO_WAIT_COMPLETED: str = "asyncio.wait completed. Done tasks: {done_tasks}, Pending tasks: {pending_tasks}"
    LOG_INTERACTOR_CANCELLED_PENDING_TASK: str = "Cancelled pending task: {task_id}"
    LOG_INTERACTOR_TIMEOUT_CLICK_RESPONSE: str = "Timeout waiting for response after clicking '{button_text}' - 'done' set is empty."
    LOG_INTERACTOR_SUCCESS_RESPONSE: str = "Successfully received response: message {message_id}"
    LOG_INTERACTOR_EXCEPTION_WAITING_RESPONSE: str = "An exception occurred while waiting for a response: {e}"
    LOG_INTERACTOR_CANCELLED_TASK_EXCEPTION: str = "Cancelled task {task_id} in exception handler."

    # New logger messages for shop.py
    LOG_SHOP_MESSAGE_CONTENT_BEFORE_CLICK: str = "Message content before clicking '{action_button}':\n{message_text}"

strings = Strings()
