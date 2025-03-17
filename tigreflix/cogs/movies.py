import discord
import asyncio
import time
from discord.ext import commands
from discord import app_commands
from tigreflix.movie_api import search_movies  # Import function to fetch movies

class MovieCommands(commands.Cog):
    """Commands related to movie management"""

    def __init__(self, bot):
        self.bot = bot  # Store bot instance
        self.cache = {}  # Initialize cache for autocomplete

    async def movie_autocomplete(self, interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice]:
        if len(current) < 3:
            return []

        current_time = time.time()
        cache_expiry = 300

        # Check if the query is in the cache and not expired
        if current in self.cache and current_time < self.cache[current][1]:
            movies = self.cache[current][0]  # Use cached results
        else:
            movies = search_movies(current)
            self.cache[current] = (movies, current_time + cache_expiry)  # Cache the results

        if not movies:
            return []

        return [
            discord.app_commands.Choice(name=movie["Title"], value=movie["Title"])
            for movie in movies[:25]
        ]

    @commands.hybrid_command(name="addmovie", description="Adiciona um filme à lista com nome corrigido e capa")
    @app_commands.describe(query="O nome do filme que você deseja adicionar")
    @app_commands.autocomplete(query=movie_autocomplete)
    async def addmovie(self, ctx: commands.Context, *, query: str):
        """Adiciona um filme à lista com nome corrigido e capa"""
        if len(query) > 100:
            await ctx.send("⚠️ Invalid movie name. Length can't be more than 100 characters", ephemeral=True)
            return

        await ctx.defer()  # Indica que o bot está processando a solicitação
        await asyncio.sleep(2)  # Adiciona um atraso de 2 segundos

        resultados = search_movies(query)
        if not resultados:
            await ctx.send("⚠️ No movies found with that name!", ephemeral=True)
            return

        # Limitar a 3 resultados para simplificar
        resultados = resultados[:3]

        # Criar mensagem com os resultados
        embed = discord.Embed(title="🎬 Search Results  ", color=discord.Color.blue())
        for i, movie in enumerate(resultados, start=1):
            embed.add_field(name=f"{i}. {movie['Title']} ({movie['Year']})", value="\u200b", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    """Registers this Cog with the bot"""
    await bot.add_cog(MovieCommands(bot))
