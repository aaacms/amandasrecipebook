# Amanda's Recipe Book

Aplicacao para importar receitas a partir de links de video. O FastAPI entrega a API e tambem os arquivos compilados do front-end; portanto, no servidor apenas o Uvicorn permanece em execucao.

As receitas importadas sao armazenadas no banco SQLite `api/recipes.db`. Para usar
outro local, defina `RECIPES_DATABASE_PATH` no arquivo `api/.env`.

## Rodar no mini PC / servidor

Instale Node.js e Python 3.11 ou mais recente no servidor. Na primeira vez, instale as dependencias e gere o front-end:

```powershell
cd my-recipe-app
npm install
npm run build

cd ..\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie o arquivo `api/.env` a partir de `api/.env.example` e informe a chave usada pelo extrator:

```env
GEMINI_API_KEY=sua_chave_aqui
```

Inicie o unico servico da aplicacao:

```powershell
cd api
.\.venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000
```

Abra `http://IP_DO_MINI_PC:8000` em outro dispositivo da mesma rede.

- Front-end: `http://IP_DO_MINI_PC:8000/`
- API: `POST http://IP_DO_MINI_PC:8000/recipes` para importar e `GET http://IP_DO_MINI_PC:8000/recipes` para listar as receitas salvas.
- Verificacao de saude: `http://IP_DO_MINI_PC:8000/health`

## Atualizar o front-end

Sempre que alterar arquivos em `my-recipe-app`, gere o build novamente antes de reiniciar o Uvicorn:

```powershell
cd my-recipe-app
npm run build
```

O diretorio `my-recipe-app/dist` e lido pelo FastAPI e nao precisa de um servidor Node.js em execucao.
