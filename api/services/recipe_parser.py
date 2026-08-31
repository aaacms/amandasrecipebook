"""Convert media metadata into a structured recipe using Gemini."""
 
import json
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    quantity: int | float | str | None = None
    unit: str | None = None


MetricSource = Literal["description", "transcript", "estimated", "user"]
RecipeCategory = Literal["breakfast", "meal", "snack", "dessert", "drink", "holiday"]


class SourcedServings(BaseModel):
    """Serving count and the origin used to determine it."""

    model_config = ConfigDict(extra="ignore")

    value: int | float = Field(description="Serving count extracted or cautiously estimated; never null.")
    source: MetricSource


class SourcedMinutes(BaseModel):
    """Duration in minutes and the origin used to determine it."""

    model_config = ConfigDict(extra="ignore")

    value: int | float = Field(
        description="Positive duration in minutes extracted or cautiously estimated; never null."
    )
    source: MetricSource


class SourcedCategory(BaseModel):
    """Recipe category and the origin used to determine it."""

    model_config = ConfigDict(extra="ignore")

    value: RecipeCategory | None = None
    source: MetricSource


class ParsedRecipe(BaseModel):
    model_config = ConfigDict(extra="ignore")

    servings: SourcedServings
    prep_time_minutes: SourcedMinutes
    cook_time_minutes: SourcedMinutes
    category: SourcedCategory
    ingredients: list[Ingredient] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class RecipeParsingError(RuntimeError):
    """Raised when Gemini cannot parse a recipe description."""


def parse_recipe(title: str, description: str) -> dict[str, Any]:
    """Parse a recipe from metadata while preserving each metric's provenance."""
    # Carrega a chave sem incluir credenciais no codigo-fonte.
    load_dotenv(Path(__file__).parents[1] / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RecipeParsingError("GEMINI_API_KEY nao foi encontrada no arquivo .env.")
    if not description.strip():
        raise ValueError("A descricao da receita esta vazia; nao ha dados para extrair.")

    prompt = f"""
        Extraia uma receita a partir do texto abaixo.

        Regras obrigatorias:
        - Para category, retorne sempre um objeto com value e source. Infira o value
          usando somente: breakfast, meal, snack, dessert, drink ou holiday. Como a
          categoria e inferida nesta solicitacao, use source "estimated".
        - Para servings, prep_time_minutes e cook_time_minutes, retorne sempre um objeto
          com value e source; value nunca pode ser null. Extraia o value quando ele
          estiver explicito na descricao e use source "description". Quando nao estiver
          explicito, obrigatoriamente faca uma estimativa cautelosa baseada somente no
          titulo e na descricao e use source "estimated". Tempos devem ser numeros de
          minutos positivos.
        - As origens permitidas sao somente description, transcript, estimated e user.
          Nesta solicitacao, nao ha transcript nem dado fornecido pelo usuario; portanto,
          use apenas description ou estimated.
        - Nunca invente ou estime ingredientes, quantidades, unidades ou instrucoes.
          Para dados ausentes, use null nos campos opcionais do ingrediente e mantenha
          ingredients ou instructions vazios quando nao houver itens na fonte.
        - Nao interprete conhecimento culinario externo como ingrediente ou instrucao.
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
