import asyncio
from random import choice
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import json
import os
import requests
from dotenv import load_dotenv
from urllib.parse import quote
import logging

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configurar intents do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Nome do arquivo onde os filmes são armazenados
ARQUIVO_FILMES = "filmes.json"

# Função para carregar os filmes do arquivo JSON
def carregar_filmes():
    if os.path.exists(ARQUIVO_FILMES):
        with open(ARQUIVO_FILMES, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Função para salvar os filmes no arquivo JSON
def salvar_filmes(filmes):
    with open(ARQUIVO_FILMES, "w", encoding="utf-8") as f:
        json.dump(filmes, f, indent=4, ensure_ascii=False)

# Carregar filmes ao iniciar
filmes = carregar_filmes()

# Função para buscar filmes usando a API OMDB
def buscar_filmes(query):
    try:
        url = f"http://www.omdbapi.com/?s={quote(query)}&apikey={OMDB_API_KEY}"
        resposta = requests.get(url).json()
        if resposta.get("Response") == "True":
            return resposta["Search"]  # Retorna a lista de filmes
    except Exception as e:
        logging.error(f"Erro ao buscar filmes: {e}")
    return []  # Retorna uma lista vazia se não encontrar ou houver erro

'''
# Função para buscar detalhes de um filme usando a API OMDB
def buscar_detalhes_filme(nome):
    try:
        url = f"http://www.omdbapi.com/?t={quote(nome)}&apikey={OMDB_API_KEY}"
        resposta = requests.get(url).json()
        if resposta.get("Response") == "True":
            return resposta  # Retorna os detalhes do filme
    except Exception as e:
        logging.error(f"Erro ao buscar detalhes do filme: {e}")
    return []  # Retorna None se não encontrar ou houver erro
'''
# Classe para criar botões de seleção de filmes
class SelecionarFilmeView(View):
    def __init__(self, filmes, ctx):
        super().__init__(timeout=30)
        self.filmes = filmes
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.ctx.author

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary)
    async def selecionar_1(self, interaction: discord.Interaction, button: Button):
        await self.processar_selecao(interaction, 0)

    @discord.ui.button(label="2", style=discord.ButtonStyle.primary)
    async def selecionar_2(self, interaction: discord.Interaction, button: Button):
        await self.processar_selecao(interaction, 1)

    @discord.ui.button(label="3", style=discord.ButtonStyle.primary)
    async def selecionar_3(self, interaction: discord.Interaction, button: Button):
        await self.processar_selecao(interaction, 2)

    async def processar_selecao(self, interaction: discord.Interaction, index: int):
        if index >= len(self.filmes):
            await interaction.response.send_message("⚠️ Seleção inválida!", ephemeral=True)
            return

        filme_selecionado = self.filmes[index]
        detalhes = buscar_filmes(filme_selecionado["Title"])

        if not detalhes:
            await interaction.response.send_message("⚠️ Não foi possível obter detalhes do filme.", ephemeral=True)
            return

        # Verificar se o filme já está na lista
        if any(f["nome"].lower() == detalhes["Title"].lower() for f in filmes):
            await interaction.response.send_message(f'⚠️ O filme "**{detalhes["Title"]}**" já está na lista!', ephemeral=True)
            return

        filme_data = {
            "nome": detalhes["Title"],
            "adicionado_por": self.ctx.author.name,
            "assistido": False,
            "capa": detalhes.get("Poster", None)
        }

        filmes.append(filme_data)
        salvar_filmes(filmes)

        mensagem = f'🎬 Filme "**{detalhes["Title"]}**" adicionado por {self.ctx.author.name}!'
        if detalhes.get("Poster"):
            await interaction.response.send_message(mensagem)
            await interaction.followup.send(detalhes["Poster"])
        else:
            await interaction.response.send_message(mensagem)

        self.stop()

    async def on_timeout(self):
        await self.ctx.send("⏰ Tempo esgotado! Nenhum filme foi selecionado.")

@bot.hybrid_command(name="addfilme", description="Adiciona um filme à lista com nome corrigido e capa")
@app_commands.describe(query="O nome do filme que você deseja adicionar")
async def addfilme(ctx: commands.Context, *, query: str):
    """Adiciona um filme à lista com nome corrigido e capa"""
    if len(query) > 100:
        await ctx.send("⚠️ Nome do filme inválido! O nome deve ter no máximo 100 caracteres.", ephemeral=True)
        return

    await ctx.defer()  # Indica que o bot está processando a solicitação
    await asyncio.sleep(2)  # Adiciona um atraso de 2 segundos

    resultados = buscar_filmes(query)
    if not resultados:
        await ctx.send("⚠️ Nenhum filme encontrado com esse nome.", ephemeral=True)
        return

    # Limitar a 3 resultados para simplificar
    resultados = resultados[:3]

    # Criar mensagem com os resultados
    embed = discord.Embed(title="🎬 Resultados da Busca", color=discord.Color.blue())
    for i, filme in enumerate(resultados, start=1):
        embed.add_field(name=f"{i}. {filme['Title']} ({filme['Year']})", value="\u200b", inline=False)

    # Adicionar botões para seleção
    view = SelecionarFilmeView(resultados, ctx)
    await ctx.send(embed=embed, view=view)

# Comando híbrido para listar filmes
@bot.hybrid_command(name="listar", description="Lista todos os filmes organizadamente")
async def listar(ctx: commands.Context):
    """Lista todos os filmes organizadamente"""
    if not filmes:
        await ctx.send("🎬 Nenhum filme adicionado ainda!", ephemeral=True)
        return

    assistidos = [f for f in filmes if f["assistido"]]
    nao_assistidos = [f for f in filmes if not f["assistido"]]

    embed = discord.Embed(title="🎬 Lista de Filmes", color=discord.Color.blue())

    if nao_assistidos:
        embed.add_field(name="📌 Para assistir", value="\n".join([f"🔹 *{f['nome']}* (Adicionado por {f['adicionado_por']})" for f in nao_assistidos]), inline=False)

    if assistidos:
        embed.add_field(name="✅ Já assistidos", value="\n".join([f"✔️ *{f['nome']}* (Adicionado por {f['adicionado_por']})" for f in assistidos]), inline=False)

    await ctx.send(embed=embed)

# Comando híbrido para remover um filme
@bot.hybrid_command(name="remover", description="Remove um filme da lista")
@app_commands.describe(filme="O nome do filme que você deseja remover")
async def remover(ctx: commands.Context, *, filme: str):
    """Remove um filme da lista"""
    filme_encontrado = encontrar_filme_por_nome(filme)
    if filme_encontrado:
        filmes.remove(filme_encontrado)
        salvar_filmes(filmes)
        await ctx.send(f'🗑️ Filme "{filme}" removido com sucesso!')
    else:
        await ctx.send(f'⚠️ Filme "{filme}" não encontrado na lista.', ephemeral=True)

# Comando híbrido para marcar um filme como assistido
@bot.hybrid_command(name="assistido", description="Marca um filme como assistido")
@app_commands.describe(filme="O nome do filme que você deseja marcar como assistido")
async def assistido(ctx: commands.Context, *, filme: str):
    """Marca um filme como assistido"""
    filme_encontrado = encontrar_filme_por_nome(filme)
    if filme_encontrado:
        filme_encontrado["assistido"] = True
        salvar_filmes(filmes)
        await ctx.send(f'✅ Filme "{filme}" marcado como assistido!')
    else:
        await ctx.send(f'⚠️ Filme "{filme}" não encontrado na lista.', ephemeral=True)

# Comando híbrido para sortear um filme
@bot.hybrid_command(name="sortear", description="Sorteia um filme ainda não assistido")
async def sortear(ctx: commands.Context):
    """Sorteia um filme ainda não assistido"""
    nao_assistidos = [f for f in filmes if not f["assistido"]]
    if nao_assistidos:
        filme_sorteado = choice(nao_assistidos)
        mensagem = f'🎲 O filme sorteado é: **{filme_sorteado["nome"]}** (Adicionado por {filme_sorteado["adicionado_por"]})!'
        if filme_sorteado.get("capa"):
            await ctx.send(mensagem)
            await ctx.send(filme_sorteado["capa"])
        else:
            await ctx.send(mensagem)
    else:
        await ctx.send("⚠️ Todos os filmes já foram assistidos! Adicione mais filmes.", ephemeral=True)

# Função para encontrar um filme pelo nome
def encontrar_filme_por_nome(nome):
    for f in filmes:
        if f["nome"].lower() == nome.lower():
            return f
    return None

@bot.hybrid_command(name="infofilme", description="Exibe informações detalhadas de um filme")
@app_commands.describe(filme="O nome do filme que você deseja buscar")
async def infofilme(ctx: commands.Context, *, filme: str):
    """Busca e exibe informações detalhadas de um filme"""
    detalhes = buscar_filmes(filme)
    
    if not detalhes:
        await ctx.send(f'⚠️ Não foi possível encontrar detalhes para "{filme}".', ephemeral=True)
        return
    
    embed = discord.Embed(
        title=detalhes["Title"],
        description=detalhes.get("Plot", "Sem descrição disponível."),
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🗓️ Ano", value=detalhes.get("Year", "Desconhecido"), inline=True)
    embed.add_field(name="🎭 Gênero", value=detalhes.get("Genre", "Desconhecido"), inline=True)
    embed.add_field(name="🎬 Diretor", value=detalhes.get("Director", "Desconhecido"), inline=False)
    embed.add_field(name="⭐ Nota IMDb", value=detalhes.get("imdbRating", "N/A"), inline=True)
    embed.add_field(name="📜 Classificação", value=detalhes.get("Rated", "N/A"), inline=True)
    embed.add_field(name="⏳ Duração", value = detalhes.get("Runtime","N/A"), inline=True)
    
    if detalhes.get("Poster") and detalhes["Poster"] != "N/A":
        embed.set_thumbnail(url=detalhes["Poster"])
    
    await ctx.send(embed=embed)


@bot.hybrid_command(name="ajuda", description="Exibe instruções sobre como usar o bot")
async def ajuda(ctx: commands.Context):
    """Exibe instruções sobre como usar o bot"""
    embed = discord.Embed(
        title="📜 Instruções para Usar o TigreFlix Bot",
        description="Aqui estão todos os comandos disponíveis e como usá-los:",
        color=discord.Color.blue()
    )

    # Adicionar campos para cada comando
    embed.add_field(
        name="🎬 Adicionar um Filme",
        value="Use `/addfilme query: Nome do Filme` para adicionar um filme à lista. O bot buscará o filme e permitirá que você selecione a opção correta.",
        inline=False
    )

    embed.add_field(
        name="📋 Listar Filmes",
        value="Use `/listar` para ver todos os filmes na lista, separados em 'Para assistir' e 'Já assistidos'.",
        inline=False
    )

    embed.add_field(
        name="🗑️ Remover um Filme",
        value="Use `/remover filme: Nome do Filme` para remover um filme da lista.",
        inline=False
    )

    embed.add_field(
        name="✅ Marcar um Filme como Assistido",
        value="Use `/assistido filme: Nome do Filme` para marcar um filme como assistido.",
        inline=False
    )

    embed.add_field(
        name="🎲 Sortear um Filme",
        value="Use `/sortear` para sortear um filme que ainda não foi assistido.",
        inline=False
    )

    embed.add_field(
        name="🛠️ Ver Comandos Disponíveis",
        value="Use `/ajuda` para ver esta mensagem novamente.",
        inline=False
    )

    # Adicionar uma nota final
    embed.set_footer(text="Dúvidas? É só chamar! 🎥🍿")

    # Enviar a mensagem
    await ctx.send(embed=embed) 

    
@bot.event
async def on_ready():
    logging.info(f'🤖 Bot {bot.user} está online!')
    try:
        synced = await bot.tree.sync()
        logging.info(f"✅ {len(synced)} comandos sincronizados.")
    except Exception as e:
        logging.error(f"Erro ao sincronizar comandos: {e}")

bot.run(TOKEN)