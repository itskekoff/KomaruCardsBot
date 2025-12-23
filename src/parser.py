import re
from .models import ParsedMessage, MessageType, strings
from .utils import clean_and_convert_to_int, remove_formatting

def parse_message(text: str) -> ParsedMessage:
    text = remove_formatting(text)
    text = text.replace('\u200b', '')

    # --- card ---
    card_pattern = re.compile(
        rf".*?(?:{strings.KEYWORD_CARD_FOUND}|{strings.KEYWORD_CARD_COLLECTION_ADDED}|{strings.KEYWORD_CARD_NEW_INTRO}|{strings.KEYWORD_CARD_GENERIC}|{strings.KEYWORD_CARD_BOOSTER_SUCCESS}) «(.+?)»(?: {strings.KEYWORD_CARD_SUFFIX_ALREADY_HAVE}|{strings.KEYWORD_CARD_SUFFIX_REPEATED}|{strings.KEYWORD_CARD_SUFFIX_ALREADY_IN_COLLECTION}|{strings.KEYWORD_CARD_SUFFIX_YOURS})?.*?\n\n"
        rf".*?{strings.KEYWORD_RARITY_TEXT} • (.+?)\n"
        rf".*?{strings.KEYWORD_POINTS_TEXT} • [+-]?[\d,]+ \[(.+)]\n"
        rf".*?{strings.KEYWORD_COINS_TEXT} • [+-]?[\d,]+ \[(.+)]"
        rf"(?:\n.*?{strings.KEYWORD_BOOSTER_USED_TEXT}.*)?" , # Optional booster line
        re.MULTILINE
    )
    card_match = card_pattern.search(text)
    if card_match:
        is_duplicate = any(keyword in text for keyword in [
            strings.KEYWORD_CARD_SUFFIX_ALREADY_HAVE,
            strings.KEYWORD_CARD_SUFFIX_REPEATED,
            strings.KEYWORD_CARD_SUFFIX_ALREADY_IN_COLLECTION
        ])
        card_type = MessageType.DUPLICATE_CARD if is_duplicate else MessageType.NEW_CARD
        return ParsedMessage(type=card_type, details={
            "name": card_match.group(1),
            "rarity": card_match.group(2),
            "total_points": clean_and_convert_to_int(card_match.group(3)),
            "total_coins": clean_and_convert_to_int(card_match.group(4)),
            "booster_used": strings.BOOSTER_LUCK if strings.KEYWORD_BOOSTER_USED_TEXT in text else None
        })

    # --- profile ---
    profile_pattern = re.compile(
        rf"{strings.KEYWORD_PROFILE_TITLE}.+?\n\n"
        rf".*?{strings.KEYWORD_COINS_TEXT} • ([\d,]+)", re.DOTALL
    )
    profile_match = profile_pattern.search(text)
    if profile_match:
        return ParsedMessage(type=MessageType.PROFILE_INFO, details={
            "total_coins": clean_and_convert_to_int(profile_match.group(1))
        })

    # --- cooldown ---
    cooldown_pattern = re.compile(
        rf"(?:{strings.KEYWORD_COOLDOWN}|{strings.KEYWORD_COOLDOWN_2}|{strings.KEYWORD_COOLDOWN_3}|{strings.KEYWORD_COOLDOWN_4}) "
        rf"(?:(\d+)ч\. )?"
        rf"(?:(\d+)мин\. )?"
        rf"(\d+)сек\."
    )
    cooldown_match = cooldown_pattern.search(text)
    if cooldown_match:
        hours_str = cooldown_match.group(1)
        minutes_str = cooldown_match.group(2)
        seconds_str = cooldown_match.group(3)

        hours = int(hours_str) if hours_str else 0
        minutes = int(minutes_str) if minutes_str else 0
        seconds = int(seconds_str) if seconds_str else 0
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return ParsedMessage(type=MessageType.COOLDOWN, details={"cooldown": total_seconds})

    # --- cooldown reduced ---
    if strings.KEYWORD_COOLDOWN_REDUCED in text:
        return ParsedMessage(type=MessageType.COOLDOWN_REDUCED)

    return ParsedMessage(type=MessageType.UNKNOWN)