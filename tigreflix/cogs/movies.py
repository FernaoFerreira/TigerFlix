import asyncio
import time
from random import choice

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from tigreflix.database import (
    add_movie,
    find_movie,
    list_movies,
    mark_watched,
    remove_movie,
)
from tigreflix.movie_api import get_movie_details, search_movies


# ── View de seleção ──────────────────────────────────────────────────────────

class SelecionarFilmeView(View):
    def __init__(self, resultados: list[dict], author: discord.User | discord.Member):
        super().__init__(timeout=30)
        self.resultados = resultados
        self.author = author
        # Cria botões dinamicamente conforme quantidade de resultados
        for i in range(len(resultados)):
            btn = Button(label=str(i + 1), style=discord.ButtonStyle.primary, custom_id=str(i))
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.author:
                await interaction.response.send_message("⚠️ Só quem pediu pode selecionar!", ephemeral=True)
                return
            await self._processar(interaction, index)
        return callback 

    async def _processar(self, interaction: discord.Interaction, index: int):
        self.stop()
        filme_escolhido = self.resultados[index]
        chosen_title = filme_escolhido["Title"]

        # Verifica duplicata antes de chamar a API de detalhes
        if find_movie(chosen_title):
            await interaction.response.edit_message(
                content=f'⚠️ "**{chosen_title}**" já está na lista!', embed=None, view=None
            )
            return

        await interaction.response.defer()

        detalhes = get_movie_details(chosen_title)
        if not detalhes:
            await interaction.followup.send("⚠️ Não foi possível obter detalhes do filme.", ephemeral=True)
            return

        poster = detalhes.get("Poster") if detalhes.get("Poster") != "N/A" else None
        added = add_movie(detalhes["Title"], interaction.user.name, poster)

        if not added:
            await interaction.followup.send(f'⚠️ "**{detalhes["Title"]}**" já está na lista!', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'🎬 {detalhes["Title"]} adicionado!',
            description=f'Adicionado por **{interaction.user.name}**',
            color=discord.Color.green(),
        )
        if poster:
            embed.set_thumbnail(url=poster)

        await interaction.edit_original_response(content=None, embed=embed, view=None)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


# ── Cog ─────────────────────────────────────────────────────────────────────

class MovieCommands(commands.Cog):
    """Comandos de gerenciamento de filmes do TigreFlix"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cache: dict[str, tuple[list, float]] = {}

    # Autocomplete compartilhado
    async def movie_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice]:
        if len(current) < 3:
            return []
        now = time.time()
        cached = self._cache.get(current)
        if cached and now < cached[1]:
            movies = cached[0]
        else:
            movies = search_movies(current)
            self._cache[current] = (movies, now + 300)
        return [
            app_commands.Choice(name=f"{m['Title']} ({m['Year']})", value=m["Title"])
            for m in movies[:25]
        ]

    # ── /addfilme ────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="addfilme", description="Adiciona um filme à lista")
    @app_commands.describe(query="Nome do filme que você quer adicionar")
    @app_commands.autocomplete(query=movie_autocomplete)
    async def addfilme(self, ctx: commands.Context, *, query: str):
        if len(query) > 100:
            await ctx.send("⚠️ Nome muito longo (máx. 100 caracteres).", ephemeral=True)
            return

        await ctx.defer()

        resultados = search_movies(query)
        if not resultados:
            await ctx.send("⚠️ Nenhum filme encontrado.", ephemeral=True)
            return

        resultados = resultados[:3]
        embed = discord.Embed(title="🎬 Resultados da Busca", color=discord.Color.blue())
        for i, m in enumerate(resultados, 1):
            embed.add_field(name=f"{i}. {m['Title']} ({m['Year']})", value="\u200b", inline=False)

        view = SelecionarFilmeView(resultados, ctx.author)
        await ctx.send(embed=embed, view=view)

    # ── /listar ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="listar", description="Lista todos os filmes")
    async def listar(self, ctx: commands.Context):
        filmes = list_movies()
        if not filmes:
            await ctx.send("🎬 Nenhum filme adicionado ainda!", ephemeral=True)
            return

        assistidos = [f for f in filmes if f["watched"]]
        nao_assistidos = [f for f in filmes if not f["watched"]]

        embed = discord.Embed(title="🎬 TigreFlix — Lista de Filmes", color=discord.Color.blue())

        if nao_assistidos:
            linhas = "\n".join(
                f"🔹 *{f['title']}* (por {f['added_by']})" for f in nao_assistidos
            )
            embed.add_field(name=f"📌 Para assistir ({len(nao_assistidos)})", value=linhas, inline=False)

        if assistidos:
            linhas = "\n".join(
                f"✔️ *{f['title']}* (por {f['added_by']})" for f in assistidos
            )
            embed.add_field(name=f"✅ Já assistidos ({len(assistidos)})", value=linhas, inline=False)

        await ctx.send(embed=embed)

    # ── /remover ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="remover", description="Remove um filme da lista")
    @app_commands.describe(filme="Nome do filme a remover")
    async def remover(self, ctx: commands.Context, *, filme: str):
        if remove_movie(filme):
            await ctx.send(f'🗑️ "**{filme}**" removido com sucesso!')
        else:
            await ctx.send(f'⚠️ "**{filme}**" não encontrado na lista.', ephemeral=True)

    # ── /assistido ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="assistido", description="Marca um filme como assistido")
    @app_commands.describe(filme="Nome do filme a marcar")
    async def assistido(self, ctx: commands.Context, *, filme: str):
        if mark_watched(filme):
            await ctx.send(f'✅ "**{filme}**" marcado como assistido!')
        else:
            await ctx.send(f'⚠️ "**{filme}**" não encontrado na lista.', ephemeral=True)

    # ── /sortear ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="sortear", description="Sorteia um filme não assistido")
    async def sortear(self, ctx: commands.Context):
        filmes = list_movies()
        nao_assistidos = [f for f in filmes if not f["watched"]]
        if not nao_assistidos:
            await ctx.send("⚠️ Todos os filmes já foram assistidos! Adicione mais.", ephemeral=True)
            return

        sorteado = choice(nao_assistidos)
        embed = discord.Embed(
            title="🎲 Filme Sorteado!",
            description=f'**{sorteado["title"]}**\nAdicionado por {sorteado["added_by"]}',
            color=discord.Color.gold(),
        )
        if sorteado.get("poster"):
            embed.set_image(url=sorteado["poster"])

        await ctx.send(embed=embed)

    # ── /infofilme ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="infofilme", description="Exibe detalhes de um filme")
    @app_commands.describe(filme="Nome do filme")
    async def infofilme(self, ctx: commands.Context, *, filme: str):
        await ctx.defer()
        detalhes = get_movie_details(filme)  # ← bug corrigido: usa get_movie_details, não search_movies

        if not detalhes:
            await ctx.send(f'⚠️ Não encontrei detalhes para "**{filme}**".', ephemeral=True)
            return

        embed = discord.Embed(
            title=detalhes["Title"],
            description=detalhes.get("Plot", "Sem sinopse disponível."),
            color=discord.Color.blue(),
        )
        embed.add_field(name="🗓️ Ano", value=detalhes.get("Year", "?"), inline=True)
        embed.add_field(name="🎭 Gênero", value=detalhes.get("Genre", "?"), inline=True)
        embed.add_field(name="⏳ Duração", value=detalhes.get("Runtime", "?"), inline=True)
        embed.add_field(name="🎬 Diretor", value=detalhes.get("Director", "?"), inline=False)
        embed.add_field(name="⭐ IMDb", value=detalhes.get("imdbRating", "N/A"), inline=True)
        embed.add_field(name="📜 Classificação", value=detalhes.get("Rated", "N/A"), inline=True)

        poster = detalhes.get("Poster")
        if poster and poster != "N/A":
            embed.set_thumbnail(url=poster)

        await ctx.send(embed=embed)

    # ── /ajuda ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="ajuda", description="Mostra os comandos disponíveis")
    async def ajuda(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📜 TigreFlix — Comandos",
            color=discord.Color.blue(),
        )
        comandos = [
            ("/addfilme [filme]", "Busca e adiciona um filme à lista"),
            ("/listar", "Mostra todos os filmes (assistidos e não assistidos)"),
            ("/remover [filme]", "Remove um filme da lista"),
            ("/assistido [filme]", "Marca um filme como assistido"),
            ("/sortear", "Sorteia um filme ainda não assistido"),
            ("/infofilme [filme]", "Exibe detalhes completos de um filme"),
            ("/ajuda", "Mostra esta mensagem"),
        ]
        for cmd, desc in comandos:
            embed.add_field(name=f"`{cmd}`", value=desc, inline=False)
        embed.set_footer(text="🎥 Bora assistir!")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MovieCommands(bot))
