import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")    

intents = discord.Intents.default()  # Create default intents
intents.message_content = True  # Enable message content if needed

bot = commands.Bot(command_prefix="!", intents=intents)  # Pass intents
