import os
import discord
from discord.ext import commands
from tigreflix.config import TOKEN
from tigreflix.database import init_db
import asyncio

# ✅ Define intents correctly
intents = discord.Intents.default()
intents.message_content = True

# ✅ Create bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync commands
    print(f"🤖 Bot {bot.user} is online!")

# ✅ Load all Cogs dynamically from 'cogs' folder
async def load_extensions():
    for filename in os.listdir("./tigreflix/cogs"):
        if filename.endswith(".py"):  # Only load .py files
            await bot.load_extension(f"tigreflix.cogs.{filename[:-3]}")  # Remove '.py'

# ✅ Main function to start bot
async def main():
    async with bot:
        init_db()  # Ensure database is initialized
        await load_extensions()  # Load all commands
        await bot.start(TOKEN)

# ✅ Start bot properly
asyncio.run(main())
