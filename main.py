import asyncio
from bot import KomaruBot

async def main():
    bot = KomaruBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
