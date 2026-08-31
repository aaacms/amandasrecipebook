"""Command-line entrypoint for recipe-extractor-cli."""
 
import json
import re
import sys
from pathlib import Path

from services.media_extractor import MediaExtractionError, extract_media_metadata
from services.recipe_parser import RecipeParsingError, parse_recipe
from services.transcription import TranscriptionError, transcribe_url


OUTPUT_DIRECTORY = Path(__file__).parent / "output"

# funcao auxiliar que transforma o titulo em um nome de arquivo seguro
def _safe_filename(title: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
    filename = filename or "receita"
    if filename.upper() in {"CON", "PRN", "AUX", "NUL"} or re.match(
        r"^(COM|LPT)[0-9]$", filename.upper()
    ):
        filename = f"_{filename}"
    return f"{filename[:50]}.json"

# recebe a URL, extrai os dados do vídeo, transforma em receita e salva em JSON
def main() -> int:
    url = input("Cole a URL da receita: ").strip()
    # se a URL estiver vazia, retorna erro
    if not url:
        print("Erro: a URL nao pode estar vazia.", file=sys.stderr)
        return 1

    # tenta
    try:
        # Busca os metadados
        media = extract_media_metadata(url)
        recipe = parse_recipe(media["title"], media["description"])
        if recipe["needs_transcription"]:
            transcript = transcribe_url(media["webpage_url"])
            recipe = parse_recipe(media["title"], media["description"], transcript)

        # Combina a origem do video com os dados extraidos da receita.
        document = {
            "source": {
                "url": media["webpage_url"],
                "author": media["uploader"],
                "platform": media["extractor"],
            },
            **recipe,
        }

        # Garante que a pasta exista e grava o JSON formatado.
        OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIRECTORY / _safe_filename(document["title"])
        output_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    # trata os erros conhecidos
    except (
        ValueError,
        MediaExtractionError,
        RecipeParsingError,
        TranscriptionError,
        OSError,
    ) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    print(f"Receita salva em: {output_path}")
    return 0

# Se este arquivo foi executado diretamente, execute main() e encerre com o return dela
if __name__ == "__main__":
    raise SystemExit(main())
