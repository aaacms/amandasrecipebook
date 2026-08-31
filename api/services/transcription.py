"""Download video audio and transcribe it with a cached Whisper model."""

from __future__ import annotations

import tempfile
from pathlib import Path
from threading import Lock

import yt_dlp
from faster_whisper import WhisperModel


class TranscriptionError(RuntimeError):
    """Raised when the audio cannot be downloaded or transcribed."""


_model: WhisperModel | None = None
_model_lock = Lock()


def _get_model() -> WhisperModel:
    """Create the CPU-friendly model once and reuse it for later requests."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_url(url: str) -> str:
    """Download the best available audio for *url* and return its transcript."""
    try:
        with tempfile.TemporaryDirectory(prefix="recipe-audio-") as temporary_directory:
            output_template = str(Path(temporary_directory) / "audio.%(ext)s")
            options = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "outtmpl": output_template,
                # No postprocessor is used: keep the source audio format intact.
            }
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)

            audio_files = [path for path in Path(temporary_directory).iterdir() if path.is_file()]
            if not audio_files:
                raise TranscriptionError("O yt-dlp nao baixou nenhum arquivo de audio.")

            segments, _ = _get_model().transcribe(str(audio_files[0]))
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            if not transcript:
                raise TranscriptionError("A transcricao do audio ficou vazia.")
            return transcript
    except TranscriptionError:
        raise
    except Exception as error:
        raise TranscriptionError(f"Erro ao transcrever o audio: {error}") from error
