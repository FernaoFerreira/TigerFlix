

# Visão Geral

### Arquitetura em Camadas

```txt
Command Layer
      ↓
Application / Service Layer
      ↓
Repository Layer + External APIs
      ↓
Database
```

Responsabilidades:

1. **Command Layer (Discord)**
    
    - recebe comandos
        
    - parseia argumentos
        
    - chama services
        
    - transforma resultado em mensagem Discord
        
2. **Service Layer (regras de negócio)**
    
    - validações
        
    - autorização
        
    - orquestração entre DB e TMDB
        
    - regras do domínio
        
3. **Repository Layer**
    
    - CRUD puro
        
    - queries ao banco
        
    - nenhuma regra de negócio
        
4. **External API Layer**
    
    - comunicação com TMDB
        
    - normalização de payloads externos
        

---

# Estrutura de Pastas

```txt
movie-bot/
│
├── app/
│   ├── __init__.py
│   │
│   ├── bot/                           # Interface com Discord
│   │   ├── commands/
│   │   │   ├── add_movie.py
│   │   │   ├── list_movies.py
│   │   │   ├── remove_movie.py
│   │   │   ├── mark_watched.py
│   │   │   ├── rate_movie.py
│   │   │   ├── suggest_movie.py
│   │   │   └── movie_details.py
│   │   │
│   │   ├── events.py
│   │   └── embeds.py                 # helpers de resposta do Discord
│   │
│   ├── core/                         # Regras de negócio e domínio
│   │   │
│   │   ├── entities/
│   │   │   ├── movie.py
│   │   │   ├── guild.py
│   │   │   └── rating.py
│   │   │
│   │   ├── services/
│   │   │   ├── add_movie_service.py
│   │   │   ├── remove_movie_service.py
│   │   │   ├── list_movies_service.py
│   │   │   ├── mark_movie_watched_service.py
│   │   │   ├── rate_movie_service.py
│   │   │   ├── suggest_movie_service.py
│   │   │   ├── search_tmdb_service.py
│   │   │   └── recommendation_service.py
│   │   │
│   │   ├── enums/
│   │   │   └── movie_status.py
│   │   │
│   │   └── exceptions.py
│   │
│   ├── infrastructure/
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   │
│   │   │   ├── schemas/
│   │   │   │   ├── movie_schema.py
│   │   │   │   ├── guild_schema.py
│   │   │   │   └── rating_schema.py
│   │   │   │
│   │   │   └── repositories/
│   │   │       ├── movie_repository.py
│   │   │       ├── guild_repository.py
│   │   │       └── rating_repository.py
│   │   │
│   │   └── tmdb/
│   │       ├── client.py
│   │       ├── dto.py
│   │       └── mapper.py
│   │
│   ├── shared/
│   │   ├── config.py
│   │   └── logging.py
│
├── migrations/
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── main.py
```

---

# Domínio (Entidades)

## Guild

Representa um servidor do Discord.

```txt
Guild
- id (interno)
- discord_id (ID do servidor)
```

Porque o bot é multi-servidor.

Cada guild tem sua própria lista de filmes.

---

## Movie

```txt
Movie
- id
- guild_id
- tmdb_id
- title
- release_year
- genres
- overview
- status
- added_by_discord_id
- created_at
```

### Regras importantes

- `tmdb_id` é o identificador real do filme
    
- `guild_id` separa servidores
    
- `added_by_discord_id` controla remoção
    
- `status` usa enum
    

---

## Rating

```txt
Rating
- id
- movie_id
- user_discord_id
- score (1–5)
- created_at
- updated_at
```

### Regras

- 1 avaliação por usuário por filme
    
- update sobrescreve nota anterior
    

Constraint:

```sql
UNIQUE(movie_id, user_discord_id)
```

---

# Enum de Status

Mesmo tendo só “assistido/não assistido”, modela como enum desde o começo.

```python
class MovieStatus(Enum):
    NOT_WATCHED = "not_watched"
    WATCHED = "watched"
```

Isso evita retrabalho depois.

---

# Banco de Dados

## movie table

```txt
movies
- id
- guild_id FK
- tmdb_id
- title
- release_year
- overview
- status
- added_by_discord_id
- created_at
```

Constraint crítica:

```sql
UNIQUE(guild_id, tmdb_id)
```

Isso impede duplicatas mesmo com concorrência.

Exemplo:

Servidor A pode ter Matrix.

Servidor B também.

Mas o mesmo servidor não duplica.

---

## ratings table

```txt
ratings
- id
- movie_id FK
- user_discord_id
- score
```

Constraint:

```sql
UNIQUE(movie_id, user_discord_id)
```

---

## guilds table

```txt
guilds
- id
- discord_id UNIQUE
```

---

# Services (Casos de Uso)

Aqui está a principal mudança.

Você estava pensando em CRUD.

Agora pensa em comportamento.

---

## AddMovieService

Responsável por:

1. buscar filme na TMDB
    
2. validar duplicata
    
3. salvar no banco
    

Fluxo:

```txt
/add Interstellar
      ↓
TMDB Search
      ↓
Usuário escolhe resultado
      ↓
Service valida duplicata
      ↓
Repository salva
```

---

## RemoveMovieService

Responsável por:

- verificar se filme existe
    
- validar permissão
    

Regra:

```txt
Pode remover se:
- adicionou o filme
OU
- é admin do Discord
```

---

## MarkMovieWatchedService

Responsável por:

- validar existência
    
- alterar status
    

Regra:

```txt
Só marca filmes já cadastrados
```

---

## RateMovieService

Responsável por:

- validar existência
    
- verificar se foi assistido
    
- inserir/atualizar nota
    

Regra:

```txt
Só pode avaliar filme assistido
```

A média **não é armazenada**.

É calculada em query:

```sql
AVG(score)
```

Mais simples e menos chance de inconsistência.

---

## SuggestMovieService

Regra:

```txt
Selecionar aleatoriamente
apenas filmes NOT_WATCHED
```

Nunca sugerir assistidos.

---

## RecommendationService

Fluxo mínimo:

1. pegar filmes assistidos
    
2. pegar melhores notas
    
3. identificar gêneros favoritos
    
4. buscar similares na TMDB
    

Exemplo:

```txt
Usuário avaliou:

Sci-fi → 5
Sci-fi → 4
Drama → 2

Resultado:
priorizar Sci-fi
```

---

# Exceptions

```python
MovieAlreadyExistsError
MovieNotFoundError
PermissionDeniedError
MovieNotWatchedError
InvalidRatingError
```

Evita if espalhado.

Exemplo:

```python
raise MovieAlreadyExistsError()
```

Command layer traduz:

```txt
❌ Esse filme já está na lista.
```

---

# Fluxo de Dependências

Regra de ouro:

```txt
bot
 ↓
core
 ↓
infrastructure
```

Nunca ao contrário.

**ERRADO**

```txt
repository importando service
```

**ERRADO**

```txt
service chamando Discord API
```

**CERTO**

```txt
command
    ↓
service
    ↓
repository
```

O service retorna dados.

A command decide como mostrar no Discord.

---
