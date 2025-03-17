# commands.py
import discord
from discord.ext import commands
from movie_api import search_movies
from database import add_movie

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)



@bot.hybrid_command(name="addmovie", description="Adds a movie to the list")
async def addmovie(ctx, *, title: str):
    results = search_movies(title)
    if results:
        movie_title = results[0]["Title"]
        add_movie(movie_title, ctx.author.name)
        await ctx.send(f"🎬 Movie \"{movie_title}\" added by {ctx.author.name}!")
    else:
        await ctx.send("⚠️ No movie found!")

def setup(bot):
    bot.add_command(addmovie)