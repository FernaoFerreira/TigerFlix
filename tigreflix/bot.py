import asyncio
import logging
import os

import discord
from discord.ext import commands

from tigreflix.config import TOKEN
from tigreflix.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        logging.info(f"🤖 {bot.user} online | {len(synced)} comandos sincronizados.")
    except Exception as e:
        logging.error(f"Erro ao sincronizar comandos: {e}")


async def load_extensions():
    cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            ext = f"tigreflix.cogs.{filename[:-3]}"
            await bot.load_extension(ext)
            logging.info(f"✅ Cog carregado: {ext}")


async def main():
    async with bot:
        init_db()
        await load_extensions()
        await bot.start(TOKEN)


asyncio.run(main())
