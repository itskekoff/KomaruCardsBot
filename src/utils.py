import re
import asyncio
import random
from telethon.tl.custom import Button
from telethon.tl.custom.message import Message

def get_message_text(message: Message) -> str | None:
    if not message:
        return None
    return message.text

def clean_and_convert_to_int(s: str) -> int:
    return int(s.replace(',', '').replace(' ', ''))

def remove_formatting(text: str) -> str:
    return re.sub(r'(\*\*|__|\*|`|```)', '', text)

def find_button_by_text(message: Message, text: str) -> Button | None:
    if not message or not message.buttons:
        return None
    
    for row in message.buttons:
        for button in row:
            if button.text.startswith(text):
                return button
    return None

async def human_delay(min_sec=0.6, max_sec=3.2):
    await asyncio.sleep(random.uniform(min_sec, max_sec))
