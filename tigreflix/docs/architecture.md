O projeto TigreFlix segue uma arquitetura em camadas simples, com o objetivo de manter comandos do Discord separados das regras de negocio e da persistencia.

Fluxo principal de dependencias:

```txt
cogs/movies.py
    -> services/movieservice.py
        -> repositories/movierepository.py
            -> database.py

services/movieservice.py
    -> movie_api.py
```

## Camadas

### Camada de Comando

Arquivo: `tigreflix/cogs/movies.py`

Responsabilidades:

- receber comandos do Discord;
- validar contexto do Discord, como servidor atual e permissoes do usuario;
- pegar `guild_id` a partir de `ctx.guild.id` ou `interaction.guild.id`;
- pegar o ID estavel do usuario a partir de `ctx.author.id` ou `interaction.user.id`;
- montar mensagens, embeds e respostas para o Discord;
- chamar apenas a camada de servico para fluxos de filmes.

Esta camada pode importar Discord. As outras camadas nao devem depender de Discord.

Quando um comando de lista de filmes e usado em DM, sem servidor, o bot responde que deve ser usado dentro de um servidor Discord.

### Camada de Servico

Arquivo: `tigreflix/services/movieservice.py`

Responsabilidades:

- aplicar regras de negocio;
- orquestrar chamadas entre repositorio e API externa;
- validar duplicidade de filmes por servidor;
- aplicar permissao de remocao;
- manter a camada de comando fina.

Funcoes principais:

- `add_movie_to_list(guild_id, title, added_by_discord_id)`
- `get_movie_list(guild_id)`
- `remove_movie_from_list(guild_id, title, requester_discord_id, is_admin)`
- `mark_movie_as_watched(guild_id, title)`
- `suggest_unwatched_movie(guild_id)`
- `get_movie_details_by_title(title)`
- `search_and_select_movie(query)`

A camada de servico nao importa Discord e nao monta embeds.

Regra atual de remocao:

- um filme so pode ser removido por quem adicionou o filme;
- ou por um administrador do servidor Discord;
- o calculo de `is_admin` fica em `cogs/movies.py`;
- a decisao de permitir ou negar a remocao fica em `movieservice.py`.

### Camada de Repositorio

Arquivo: `tigreflix/repositories/movierepository.py`

Responsabilidades:

- executar CRUD puro no SQLite;
- filtrar consultas por `guild_id`;
- retornar dados como dicionarios simples;
- nao conter regra de negocio;
- nao importar Discord;
- nao chamar API externa.

Funcoes principais:

- `add_movie(guild_id, title, added_by_discord_id, poster)`
- `find_movie(guild_id, title)`
- `list_movies(guild_id)`
- `remove_movie(guild_id, title)`
- `mark_watched(guild_id, title)`

Todas as consultas relevantes usam `guild_id`, permitindo que cada servidor Discord tenha sua propria lista de filmes.

### Infraestrutura / Banco de Dados

Arquivo: `tigreflix/database.py`

Responsabilidades:

- fornecer conexao SQLite com `get_conn`;
- inicializar tabelas com `init_db`;
- aplicar migracoes seguras em bancos existentes;
- migrar dados legados de `filmes.json`, quando existir.

O caminho do banco e configurado por variavel de ambiente:

```python
DB_PATH = os.getenv("DB_PATH", "tigreflix.db")
```

Se `DB_PATH` nao for definido, o projeto usa `tigreflix.db`.

Migracoes atuais:

- adiciona `guild_id` em `movies`, se a coluna ainda nao existir;
- adiciona `added_by_discord_id` em `movies`, se a coluna ainda nao existir;
- preserva dados existentes;
- remove a restricao antiga de titulo unico global quando necessario, usando `UNIQUE(guild_id, title)` para permitir o mesmo filme em servidores diferentes.

### Camada de API Externa

Arquivo: `tigreflix/movie_api.py`

Responsabilidades:

- consultar a API OMDB;
- retornar dados brutos ou normalizados para a camada de servico.

A API externa nao deve ser chamada diretamente por `cogs/movies.py` nos fluxos principais de filmes.

## Modelo atual de filme

A tabela `movies` mantem os campos principais:

```txt
id
guild_id
title
added_by
added_by_discord_id
watched
poster
```

Observacoes:

- `guild_id` separa as listas por servidor Discord;
- `added_by_discord_id` guarda o ID estavel do usuario que adicionou o filme;
- `added_by` permanece para compatibilidade com dados antigos e exibicao de fallback;
- novos filmes salvam o ID do usuario em `added_by_discord_id`.

## Estado atual

Ja implementado:

- fluxo de adicao passando pela camada de servico;
- listagem, remocao, marcar como assistido e sorteio usando `guild_id`;
- isolamento das listas por servidor Discord;
- armazenamento de ID de usuario Discord para novas adicoes;
- permissao de remocao por autor original ou administrador;
- `DB_PATH` configuravel por variavel de ambiente;
- migracoes seguras para bancos SQLite existentes.

Ainda nao implementado:

- ratings;
- tabela `guilds`;
- migracao de OMDB para TMDB;
- excecoes customizadas;
- reorganizacao de pastas;
- entidades de dominio formais.
