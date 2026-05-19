# 🐯 TigreFlix

Bot do Discord para o grupo gerenciar a lista de filmes pra assistir juntos.

## Estrutura

```
tigreflix/
├── bot.py          # Ponto de entrada
├── config.py       # Variáveis de ambiente
├── database.py     # SQLite (CRUD + migração do JSON)
├── movie_api.py    # Integração com OMDB
└── cogs/
    └── movies.py   # Todos os comandos slash
```

## Instalação

```bash
pip install -r requirements.txt
```
Crie um arquivo `.env` na raiz do projeto:

```
DISCORD_TOKEN=seu_token_aqui
OMDB_API_KEY=sua_chave_aqui
```

## Rodando

```bash
python -m tigreflix.bot
```

## Migração do filmes.json

Ao iniciar pela primeira vez, se existir um `filmes.json` na raiz, os dados são importados automaticamente para o banco SQLite (`tigreflix.db`) e o arquivo é renomeado para `filmes.json.migrado`.

## Comandos

| Comando | Descrição |
|---|---|
| `/addfilme [nome]` | Busca e adiciona um filme |
| `/listar` | Lista todos os filmes |
| `/remover [nome]` | Remove um filme |
| `/assistido [nome]` | Marca como assistido |
| `/sortear` | Sorteia um filme não assistido |
| `/infofilme [nome]` | Detalhes completos de um filme |
| `/ajuda` | Lista os comandos |
