"""Convert media metadata into a structured recipe using Gemini."""
 
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    quantity: int | float | str | None = None
    unit: str | None = None


class ParsedRecipe(BaseModel):
    model_config = ConfigDict(extra="ignore")

    servings: int | float | str | None = None
    prep_time_minutes: int | float | None = None
    cook_time_minutes: int | float | None = None
    category: str | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class RecipeParsingError(RuntimeError):
    """Raised when Gemini cannot parse a recipe description."""


def parse_recipe(title: str, description: str) -> dict[str, Any]:
    """Extract only facts present in the supplied title and description."""
    # Carrega a chave sem incluir credenciais no codigo-fonte.
    load_dotenv(Path(__file__).parents[1] / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RecipeParsingError("GEMINI_API_KEY nao foi encontrada no arquivo .env.")
    if not description.strip():
        raise ValueError("A descricao da receita esta vazia; nao ha dados para extrair.")

    prompt = f"""
        Extraia uma receita usando exclusivamente os fatos presentes no texto abaixo.

        Regras obrigatorias:
        - Nunca invente ingredientes, quantidades, tempos, porcoes ou etapas.
        - Use null para uma informacao ausente.
        - Mantenha ingredients vazio e instructions vazio quando esses dados nao aparecerem.
        - Nao interprete conhecimento culinario externo como fato.
        - Retorne somente os campos definidos no schema.

        Titulo:
        {title}

        Descricao:
        {description}
    """

    try:
        client = genai.Client(api_key=api_key)
        # O schema faz o Gemini retornar dados diretamente estruturados.
        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParsedRecipe,
            ),
        )
        # Alguns modelos retornam o JSON em text, mesmo com um schema definido.
        parsed_recipe = response.parsed
        if parsed_recipe is None and response.text:
            # Lê o primeiro objeto caso o modelo repita a resposta.
            parsed_recipe, _ = json.JSONDecoder().raw_decode(response.text.lstrip())
        if parsed_recipe is None:
            raise RecipeParsingError("A API Gemini nao retornou uma receita estruturada.")
        if isinstance(parsed_recipe, ParsedRecipe):
            return parsed_recipe.model_dump(mode="json")
        return ParsedRecipe.model_validate(parsed_recipe).model_dump(mode="json")
    except RecipeParsingError:
        raise
    except Exception as error:
        raise RecipeParsingError(f"Erro ao extrair a receita com o Gemini: {error}") from error