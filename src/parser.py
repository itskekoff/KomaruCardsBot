import re
from .models import ParsedMessage, MessageType, strings
from .utils import clean_and_convert_to_int, remove_formatting
from .nn.predict import Predictor

predictor = Predictor()

def parse_message(text: str) -> ParsedMessage:
    cleaned_text = remove_formatting(text)
    cleaned_text = cleaned_text.replace('\u200b', '')

    prediction = predictor.predict(cleaned_text)
    predicted_message_type = prediction.get('message_type')

    if predicted_message_type in ('NEW_CARD', 'DUPLICATE_CARD'):
        card_detail_pattern = re.compile(
            r"«(.+?)»[^\n]*\n\n"
            rf".*?{strings.KEYWORD_RARITY_TEXT} • (.+?)\n"
            rf".*?{strings.KEYWORD_POINTS_TEXT} • [+-]?[\d,]+ \[(.+?)]\n"
            rf".*?{strings.KEYWORD_COINS_TEXT} • [+-]?[\d,]+ \[(.+?)]" ,
            re.DOTALL
        )
        card_match = card_detail_pattern.search(cleaned_text)
        
        if card_match:
            card_type = MessageType.NEW_CARD if predicted_message_type == 'NEW_CARD' else MessageType.DUPLICATE_CARD
            return ParsedMessage(type=card_type, details={
                "name": card_match.group(1).strip(),
                "rarity": card_match.group(2).strip(),
                "total_points": clean_and_convert_to_int(card_match.group(3)),
                "total_coins": clean_and_convert_to_int(card_match.group(4)),
                "booster_used": strings.BOOSTER_LUCK if strings.KEYWORD_BOOSTER_USED_TEXT in cleaned_text else None
            })

    profile_pattern = re.compile(
        rf"{strings.KEYWORD_PROFILE_TITLE}.+?\n\n"
        rf".*?{strings.KEYWORD_COINS_TEXT} • ([\d,]+)", re.DOTALL
    )
    profile_match = profile_pattern.search(cleaned_text)
    if profile_match:
        return ParsedMessage(type=MessageType.PROFILE_INFO, details={
            "total_coins": clean_and_convert_to_int(profile_match.group(1))
        })

    cooldown_pattern = re.compile(
        rf"(?:{'|'.join(strings.KEYWORD_COOLDOWN_VARIANTS)}) "
        rf"(?:(\d+)ч\. )?"
        rf"(?:(\d+)мин\. )?"
        rf"(\d+)сек\."
    )
    cooldown_match = cooldown_pattern.search(cleaned_text)
    if cooldown_match:
        hours_str, minutes_str, seconds_str = cooldown_match.groups()
        hours = int(hours_str) if hours_str else 0
        minutes = int(minutes_str) if minutes_str else 0
        seconds = int(seconds_str) if seconds_str else 0
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return ParsedMessage(type=MessageType.COOLDOWN, details={"cooldown": total_seconds})

    if strings.KEYWORD_COOLDOWN_REDUCED in cleaned_text:
        return ParsedMessage(type=MessageType.COOLDOWN_REDUCED)

    return ParsedMessage(type=MessageType.UNKNOWN)
