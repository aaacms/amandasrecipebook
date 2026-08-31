""" Extract recipe metadata from supported social video URLs """
 
from typing import Any
from urllib.parse import urlparse

import requests
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget


class MediaExtractionError(RuntimeError):
    """Raised when yt-dlp cannot read a recipe URL."""


def _is_tiktok_url(url: str) -> bool:
    return "tiktok.com" in urlparse(url).netloc.lower()


def _extract_tiktok_oembed(url: str) -> dict[str, Any]:
    """Use TikTok's public metadata endpoint when its page is blocked."""
    response = requests.get(
        "https://www.tiktok.com/oembed", params={"url": url}, timeout=15
    )
    response.raise_for_status()
    data = response.json()
    return {
        "title": data.get("title") or "Receita sem titulo",
        "description": (data.get("title") or "").strip(),
        "uploader": data.get("author_name"),
        "webpage_url": url,
        "thumbnail": data.get("thumbnail_url"),
        "extractor": "TikTok",
    }


def _validate_url(url: str) -> None:
    # Aceita somente URLs web completas.
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("Informe uma URL valida iniciada por http:// ou https://.")


def extract_media_metadata(url: str) -> dict[str, Any]:
    """Return metadata without downloading video or audio."""
    _validate_url(url)

    if _is_tiktok_url(url):
        try:
            # Evita o erro do yt-dlp quando o TikTok bloqueia a pagina.
            return _extract_tiktok_oembed(url)
        except requests.RequestException:
            pass

    options = {
        "quiet": True,
        "no_warnings": True,
        # O primeiro passo usa apenas os metadados do video.
        "skip_download": True,
        # Ajuda o TikTok a aceitar a requisicao como um navegador real.
        "impersonate": ImpersonateTarget.from_str("chrome"),
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=False)
    except Exception as error:
        # O oEmbed pode funcionar quando a pagina do TikTok bloqueia o yt-dlp.
        if _is_tiktok_url(url):
            try:
                return _extract_tiktok_oembed(url)
            except requests.RequestException:
                pass
        message = f"Nao foi possivel ler a URL: {error}"
        if "TikTok" in str(error):
            message += (
                " O TikTok bloqueou os metadados; tente um link publico diferente."
            )
        raise MediaExtractionError(message) from error

    if not info:
        raise MediaExtractionError("O yt-dlp nao retornou dados para essa URL.")

    return {
        "title": info.get("title") or "Receita sem titulo",
        "description": (info.get("description") or "").strip(),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url") or url,
        "thumbnail": info.get("thumbnail"),
        "extractor": info.get("extractor") or info.get("ie_key"),
    }