"""Configuration and constants for YouTubeGIS."""

from __future__ import annotations

from typing import Final

# OpenRouter Configuration
OPENROUTER_BASE_URL: Final[str] = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL: Final[str] = "openai/gpt-4o-mini"
OPENROUTER_HTTP_REFERER: Final[str] = "https://github.com/aitor/YouTubeGIS"
OPENROUTER_APP_TITLE: Final[str] = "YouTubeGIS"

# Model Configuration
OPENAI_MODEL: Final[str] = OPENROUTER_MODEL
OPENAI_TEMPERATURE: Final[float] = 0.3
OPENAI_MAX_TOKENS: Final[int] = 64
OPENAI_SYSTEM_PROMPT: Final[str] = (
    "Eres un experto en geografía y análisis de títulos de vídeo. "
    "Debes devolver únicamente una localización geográfica real, priorizando el lugar principal del vídeo. "
    "Si el título menciona varios lugares, elige el más central o representativo. "
    "No inventes ubicaciones, no expliques tu razonamiento y no devuelvas texto extra."
)
OPENAI_LOCATION_PROMPT_TEMPLATE: Final[str] = (
    "Analiza este título de vídeo y devuelve solo el nombre principal de una única localización geográfica real: {title}. "
    "Prioriza el lugar más relevante del vídeo. Si no hay una ubicación clara, responde exactamente 'sin ubicación clara'."
)

# YouTube Configuration
YOUTUBE_API_VERSION: Final[str] = "v3"
YOUTUBE_SEARCH_ORDER: Final[str] = "viewCount"
YOUTUBE_SEARCH_TYPE: Final[str] = "video"

# ArcGIS Configuration
ARCGIS_PORTAL: Final[str] = "https://www.arcgis.com"
ARCGIS_GIS_PORTAL: Final[str] = ARCGIS_PORTAL
ARCGIS_FEATURE_SERVICE_TAGS: Final[list[str]] = ["geojson", "featureservice"]
ARCGIS_BASE_URL: Final[str] = f"{ARCGIS_PORTAL}/home/item.html?id="

# Geocoding Configuration
MAX_GEOCODING_RESULTS: Final[int] = 1

# File Output Configuration
OUTPUT_DIR: Final[str] = "output"
GEOJSON_ENCODING: Final[str] = "utf-8"
GEOJSON_INDENT: Final[int] = 2

# Keyring Configuration
KEYRING_SERVICE_ID: Final[str] = "YouTubeGIS"
KEYRING_OPENROUTER_KEY: Final[str] = "OPENROUTER_API_KEY"
KEYRING_OPENAI_KEY: Final[str] = KEYRING_OPENROUTER_KEY
KEYRING_LEGACY_OPENAI_KEY: Final[str] = "OPENAI_API_KEY"
KEYRING_YOUTUBE_KEY: Final[str] = "YOUTUBE_API_KEY"
KEYRING_USERNAME_KEY: Final[str] = "USERNAME"
KEYRING_PASSWORD_KEY: Final[str] = "PWD"

# Working directory for persistent YouTubeGIS data (cron context)
WORKING_DIR: Final[str] = "/home/aitor/YouTubeGIS"
FALLBACK_WORKING_DIR: Final[str] = "/tmp/YouTubeGIS"
API_KEYS_FILENAME: Final[str] = "api_keys.txt"

# Environment Variable Configuration
ENV_OPENAI_API_KEYS: Final[tuple[str, ...]] = ("OPENROUTER_API_KEY", "OPENROUTER", "OPENAI_API_KEY")
ENV_YOUTUBE_API_KEYS: Final[tuple[str, ...]] = ("YOUTUBE_API_KEY",)
ENV_ARCGIS_USERNAMES: Final[tuple[str, ...]] = ("ARCGIS_USERNAME", "USERNAME")
ENV_ARCGIS_PASSWORDS: Final[tuple[str, ...]] = ("ARCGIS_PASSWORD",)

# UI Configuration
CHANNEL_SELECTION_TITLE: Final[str] = "Elige el canal de YouTube que quieras: "
VIDEO_COUNT_TITLE: Final[str] = "Dime cuántos vídeos quieres procesar: "
DEFAULT_PICK_INDICATOR: Final[str] = " 👉 "

# Logging Configuration
LOG_FORMAT: Final[str] = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"

# String generation for filenames
RANDOM_STRING_LENGTH: Final[int] = 8
TIMESTAMP_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
