"""FastAPI application for extracting recipes from social-video URLs."""

import json
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from services.media_extractor import MediaExtractionError, extract_media_metadata
from services.recipe_parser import RecipeParsingError, parse_recipe
from services.transcription import TranscriptionError, transcribe_url


OUTPUT_DIRECTORY = Path(__file__).parent / "output"
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
    """Resultado da receita extraida e o local onde ela foi salva."""

    recipe: dict
    output_file: str


def _safe_filename(title: str) -> str:
    """Transforma o titulo em um nome de arquivo seguro no Windows."""
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
    filename = filename or "receita"
    if filename.upper() in {"CON", "PRN", "AUX", "NUL"} or re.match(
        r"^(COM|LPT)[0-9]$", filename.upper()
    ):
        filename = f"_{filename}"
    return f"{filename[:50]}.json"


def extract_recipe(url: str) -> tuple[dict, Path]:
    """Extract, parse and persist a recipe, returning it with its JSON path."""
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
        },
        **recipe,
    }
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIRECTORY / _safe_filename(document["title"])
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return document, output_path


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(payload: RecipeRequest) -> RecipeResponse:
    """Extrai uma receita de uma URL de video publica."""
    try:
        recipe, output_path = extract_recipe(str(payload.url))
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

    relative_path = output_path.relative_to(Path(__file__).parent)
    return RecipeResponse(recipe=recipe, output_file=str(relative_path))


# Em producao, o FastAPI tambem entrega o build do Vite. Monte isto por ultimo
# para que as rotas da API acima continuem tendo prioridade.
if FRONTEND_DIRECTORY.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
