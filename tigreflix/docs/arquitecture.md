O projeto TigreFlix será refatorado para seguir uma arquitetura de camadas clara, com o seguinte fluxo de dependência:

**Camada de Comando (`command layer`):**
- `tigreflix/cogs/movies.py`: Responsável por lidar com os comandos do Discord. Irá interagir EXCLUSIVAMENTE com a `Camada de Serviço`.

**Camada de Serviço (`service layer`):**
- `tigreflix/services/movieservice.py` (será criado/preenchido): Conterá a lógica de negócios e orquestrará as operações. Irá interagir com a `Camada de Repositório` e com a `Camada de API Externa`.

**Camada de Repositório (`repository layer`):**
- `tigreflix/repositories/movierepository.py`: Abstrairá o acesso aos dados do banco de dados (SQLite). Irá interagir EXCLUSIVAMENTE com a `Infraestrutura/Persistência`.

**Infraestrutura/Persistência (`database`):**
- `tigreflix/database.py`: Responsável pela inicialização do banco de dados (`init_db`), migração de dados (`_migrate_from_json`) e fornecimento da conexão (`get_conn`). As funções de CRUD foram movidas para o repositório.

**Camada de API Externa (`external API layer`):**
- `tigreflix/movie_api.py`: Responsável por interagir com APIs externas (OMDB). Irá fornecer dados brutos para a `Camada de Serviço`.

### Plano de Migração Incremental (Passo 2 de N)

O objetivo agora é introduzir a camada de serviço e mover a lógica de negócios relacionada ao fluxo de adição de filmes para ela, tornando a camada de comando mais fina.

**Passo 2: Mover o Fluxo de Adição de Filme para a Camada de Serviço**

1.  **Arquivos que serão modificados/criados:**
    - Modificar `tigreflix/cogs/movies.py`.
    - Criar (ou preencher) `tigreflix/services/movieservice.py`.

2.  **Lógica a ser movida para `tigreflix/services/movieservice.py`:**
    - A função `search_movies` (atualmente chamada diretamente em `cogs/movies.py`).
    - A lógica de validação de duplicatas (`find_movie(chosen_title)`).
    - A chamada a `get_movie_details` para obter detalhes completos do filme.
    - A chamada a `add_movie` para salvar o filme no repositório.
    - Qualquer outra lógica de orquestração relacionada à adição de filmes.

3.  **Mudanças nas Importações:**
    - Em `tigreflix/services/movieservice.py`:
        - Importar funções do repositório: `add_movie`, `find_movie` de `tigreflix/repositories/movierepository.py`.
        - Importar funções da API externa: `search_movies`, `get_movie_details` de `tigreflix/movie_api.py`.
    - Em `tigreflix/cogs/movies.py`:
        - Remover importações diretas de `tigreflix/repositories/movierepository.py` para as funções de adição (`add_movie`, `find_movie`).
        - Remover importações diretas de `tigreflix/movie_api.py` para as funções de busca (`search_movies`, `get_movie_details`).
        - Adicionar importação de `tigreflix/services/movieservice.py` para a nova função de serviço (ex: `add_movie_to_list`).

4.  **Como a funcionalidade continuará funcionando:**
    - A `SelecionarFilmeView` e o comando `/addfilme` em `cogs/movies.py` passarão a chamar uma única função no `movieservice.py` para realizar todo o fluxo de adição de filme.
    - O `movieservice.py` encapsulará a coordenação entre o repositório (`movierepository.py`) e a API externa (`movie_api.py`).
    - As outras funcionalidades do bot (`/listar`, `/remover`, etc.) permanecerão inalteradas nesta etapa, pois não serão refatoradas agora. Isso garante que o bot continue funcional durante a migração.

**Próximos passos (não serão implementados agora):**
- Mover a lógica de outros comandos para o `movieservice.py`.
- Refatorar `movie_api.py` para ser um módulo de API externa claro, sem lógica de negócios.
