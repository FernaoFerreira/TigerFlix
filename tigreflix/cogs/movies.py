import time

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from tigreflix.exceptions import (
    MovieAlreadyExistsError,
    MovieDetailsNotFoundError,
    MovieNotFoundError,
    NoUnwatchedMoviesError,
    PermissionDeniedError,
)
from tigreflix.services.movieservice import (
    add_movie_to_list,
    get_movie_details_by_title,
    get_movie_list,
    mark_movie_as_watched,
    remove_movie_from_list,
    search_and_select_movie,
    suggest_unwatched_movie,
)


# ── View de seleção ──────────────────────────────────────────────────────────

class SelecionarFilmeView(View):
    def __init__(
        self,
        resultados: list[dict],
        author: discord.User | discord.Member,
        guild_id: int,
    ):
        super().__init__(timeout=30)
        self.resultados = resultados
        self.author = author
        self.guild_id = guild_id
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

        await interaction.response.defer()

        if interaction.guild is None:
            await interaction.followup.send(
                "⚠️ Use este bot dentro de um servidor Discord.", ephemeral=True
            )
            return

        try:
            detalhes = add_movie_to_list(
                self.guild_id, chosen_title, interaction.user.id
            )
        except MovieNotFoundError:
            await interaction.followup.send("⚠️ Nenhum filme encontrado.", ephemeral=True)
            return
        except MovieAlreadyExistsError as error:
            await interaction.followup.send(
                f'⚠️ "**{error.title}**" já está na lista!', ephemeral=True
            )
            return
        except MovieDetailsNotFoundError:
            await interaction.followup.send(
                "⚠️ Não foi possível obter detalhes do filme.", ephemeral=True
            )
            return

        poster = detalhes.get("Poster") if detalhes.get("Poster") != "N/A" else None

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

    async def _require_guild(self, ctx: commands.Context) -> int | None:
        if ctx.guild is None:
            await ctx.send(
                "⚠️ Use este bot dentro de um servidor Discord.", ephemeral=True
            )
            return None
        return ctx.guild.id

    @staticmethod
    def _added_by_text(movie: dict) -> str:
        discord_id = movie.get("added_by_discord_id")
        if discord_id:
            return f"<@{discord_id}>"
        return movie["added_by"]

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
            movies = search_and_select_movie(current)
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
        guild_id = await self._require_guild(ctx)
        if guild_id is None:
            return

        if len(query) > 100:
            await ctx.send("⚠️ Nome muito longo (máx. 100 caracteres).", ephemeral=True)
            return

        await ctx.defer()

        resultados = search_and_select_movie(query)
        if not resultados:
            await ctx.send("⚠️ Nenhum filme encontrado.", ephemeral=True)
            return

        resultados = resultados[:3]
        embed = discord.Embed(title="🎬 Resultados da Busca", color=discord.Color.blue())
        for i, m in enumerate(resultados, 1):
            embed.add_field(name=f"{i}. {m['Title']} ({m['Year']})", value="\u200b", inline=False)

        view = SelecionarFilmeView(resultados, ctx.author, guild_id)
        await ctx.send(embed=embed, view=view)

    # ── /listar ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="listar", description="Lista todos os filmes")
    async def listar(self, ctx: commands.Context):
        guild_id = await self._require_guild(ctx)
        if guild_id is None:
            return

        filmes = get_movie_list(guild_id)
        if not filmes:
            await ctx.send("🎬 Nenhum filme adicionado ainda!", ephemeral=True)
            return

        assistidos = [f for f in filmes if f["watched"]]
        nao_assistidos = [f for f in filmes if not f["watched"]]

        embed = discord.Embed(title="🎬 TigreFlix — Lista de Filmes", color=discord.Color.blue())

        if nao_assistidos:
            linhas = "\n".join(
                f"🔹 *{f['title']}* (por {self._added_by_text(f)})"
                for f in nao_assistidos
            )
            embed.add_field(name=f"📌 Para assistir ({len(nao_assistidos)})", value=linhas, inline=False)

        if assistidos:
            linhas = "\n".join(
                f"✔️ *{f['title']}* (por {self._added_by_text(f)})" for f in assistidos
            )
            embed.add_field(name=f"✅ Já assistidos ({len(assistidos)})", value=linhas, inline=False)

        await ctx.send(embed=embed)

    # ── /remover ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="remover", description="Remove um filme da lista")
    @app_commands.describe(filme="Nome do filme a remover")
    async def remover(self, ctx: commands.Context, *, filme: str):
        guild_id = await self._require_guild(ctx)
        if guild_id is None:
            return

        is_admin = bool(ctx.author.guild_permissions.administrator)
        try:
            remove_movie_from_list(guild_id, filme, ctx.author.id, is_admin)
            await ctx.send(f'🗑️ "**{filme}**" removido com sucesso!')
        except PermissionDeniedError:
            await ctx.send(
                f'⚠️ Você não tem permissão para remover "**{filme}**".',
                ephemeral=True,
            )
        except MovieNotFoundError:
            await ctx.send(f'⚠️ "**{filme}**" não encontrado na lista.', ephemeral=True)

    # ── /assistido ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="assistido", description="Marca um filme como assistido")
    @app_commands.describe(filme="Nome do filme a marcar")
    async def assistido(self, ctx: commands.Context, *, filme: str):
        guild_id = await self._require_guild(ctx)
        if guild_id is None:
            return

        try:
            mark_movie_as_watched(guild_id, filme)
            await ctx.send(f'✅ "**{filme}**" marcado como assistido!')
        except MovieNotFoundError:
            await ctx.send(f'⚠️ "**{filme}**" não encontrado na lista.', ephemeral=True)

    # ── /sortear ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="sortear", description="Sorteia um filme não assistido")
    async def sortear(self, ctx: commands.Context):
        guild_id = await self._require_guild(ctx)
        if guild_id is None:
            return

        try:
            sorteado = suggest_unwatched_movie(guild_id)
        except NoUnwatchedMoviesError:
            await ctx.send("⚠️ Todos os filmes já foram assistidos! Adicione mais.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎲 Filme Sorteado!",
            description=(
                f'**{sorteado["title"]}**\n'
                f"Adicionado por {self._added_by_text(sorteado)}"
            ),
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

        try:
            detalhes = get_movie_details_by_title(filme)
        except MovieDetailsNotFoundError:
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
