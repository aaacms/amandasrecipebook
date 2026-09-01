"""FastAPI application for extracting recipes from social-video URLs."""

import os
from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from database import (
    get_recipe,
    initialize_database,
    list_recipes,
    save_recipe,
    update_recipe,
)
from services.media_extractor import MediaExtractionError, extract_media_metadata
from services.recipe_parser import RecipeParsingError, parse_recipe
from services.transcription import TranscriptionError, transcribe_url


FRONTEND_DIRECTORY = Path(__file__).parent.parent / "my-recipe-app" / "dist"
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
app = FastAPI(
    title="Amanda's Recipe Book API",
    version="1.0.0",
    description="Extrai receitas estruturadas a partir de URLs de videos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in FRONTEND_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecipeRequest(BaseModel):
    """URL publica do video que contem a receita."""

    url: HttpUrl


class RecipeResponse(BaseModel):
    """Resultado da receita extraida e seu identificador no banco de dados."""

    recipe: dict
    recipe_id: int


class SavedRecipe(BaseModel):
    """Recipe record returned by the SQLite collection."""

    id: int
    recipe: dict
    created_at: str


class RecipeUpdate(BaseModel):
    """Complete edited recipe document sent by the front-end."""

    recipe: dict


def extract_recipe(url: str) -> tuple[dict, int]:
    """Extract, parse and persist a recipe, returning it with its database ID."""
    media = extract_media_metadata(url)
    recipe = parse_recipe(media["title"], media["description"])
    if recipe["needs_transcription"]:
        transcript = transcribe_url(media["webpage_url"])
        recipe = parse_recipe(media["title"], media["description"], transcript)

    document = {
        "source": {
            "url": media["webpage_url"],
            "author": media["uploader"],
            "platform": media["extractor"],
            "thumbnail": media.get("thumbnail"),
        },
        **recipe,
    }
    return document, save_recipe(document)


@app.on_event("startup")
def create_database() -> None:
    """Ensure SQLite is ready before accepting recipe imports."""
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeRequest) -> RecipeResponse:
    """Extrai uma receita de uma URL de video publica."""
    try:
        recipe, recipe_id = extract_recipe(str(payload.url))
    except (
        ValueError,
        MediaExtractionError,
        RecipeParsingError,
        TranscriptionError,
        OSError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error

    return RecipeResponse(recipe=recipe, recipe_id=recipe_id)


@app.get("/recipes", response_model=list[SavedRecipe])
def get_recipes() -> list[dict]:
    """List all recipes saved in SQLite, newest first."""
    return list_recipes()


@app.get("/recipes/{recipe_id}", response_model=SavedRecipe)
def get_saved_recipe(recipe_id: int) -> dict:
    """Return one saved recipe by its database ID."""
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receita não encontrada.")
    return recipe


@app.put("/recipes/{recipe_id}", response_model=SavedRecipe)
def update_saved_recipe(recipe_id: int, payload: RecipeUpdate) -> dict:
    """Persist edits to a saved recipe."""
    saved_recipe = get_recipe(recipe_id)
    if saved_recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receita não encontrada.")

    recipe = deepcopy(payload.recipe)
    source = recipe.get("source")
    if not isinstance(recipe.get("title"), str) or not recipe["title"].strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Título é obrigatório.")
    if not isinstance(source, dict) or not isinstance(source.get("url"), str) or not source["url"].strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="URL de origem é obrigatória.")
    for field in ("servings", "prep_time_minutes", "cook_time_minutes"):
        metric = recipe.get(field)
        if not isinstance(metric, dict) or "value" not in metric or not metric.get("source"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} precisa de valor e source.")
        previous_metric = saved_recipe["recipe"].get(field)
        previous_value = previous_metric.get("value") if isinstance(previous_metric, dict) else previous_metric
        previous_source = previous_metric.get("source", "user") if isinstance(previous_metric, dict) else "user"
        if metric["value"] != previous_value:
            metric["source"] = "user"
        else:
            metric["source"] = previous_source
    category = recipe.get("category")
    previous_category = saved_recipe["recipe"].get("category")
    if isinstance(category, dict) and "value" in category:
        previous_category_value = previous_category.get("value") if isinstance(previous_category, dict) else previous_category
        previous_category_source = previous_category.get("source", "user") if isinstance(previous_category, dict) else "user"
        category["source"] = (
            "user"
            if category["value"] != previous_category_value
            else previous_category_source
        )
    if not update_recipe(recipe_id, recipe):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receita não encontrada.")
    return get_recipe(recipe_id)


@app.get("/recipe/{recipe_id}", include_in_schema=False)
def recipe_page(recipe_id: int) -> FileResponse:
    """Serve the front-end detail page while keeping its URL shareable."""
    index_file = FRONTEND_DIRECTORY / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Front-end não encontrado.")
    return FileResponse(index_file)


# Em producao, o FastAPI tambem entrega o build do Vite. Monte isto por ultimo
# para que as rotas da API acima continuem tendo prioridade.
if FRONTEND_DIRECTORY.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
