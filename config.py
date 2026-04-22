"""Configuration and constants for YouTubeGIS."""

from __future__ import annotations

from typing import Final

# OpenAI Configuration
OPENAI_MODEL: Final[str] = "gpt-4"
OPENAI_TEMPERATURE: Final[float] = 0.3
OPENAI_MAX_TOKENS: Final[int] = 64
OPENAI_SYSTEM_PROMPT: Final[str] = (
    "Eres un experto en geografía. Necesito que me ayudes a extraer la localización y ubicaciones "
    "de algunas cadenas de texto que te voy a pasar"
)
OPENAI_LOCATION_PROMPT_TEMPLATE: Final[str] = (
    "Identifica y escribe solo el nombre principal de la localización geográfica en el título: {title}. "
    "Si no hay una clara, no inventes nada."
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
KEYRING_OPENAI_KEY: Final[str] = "OPENAI_API_KEY"
KEYRING_YOUTUBE_KEY: Final[str] = "YOUTUBE_API_KEY"
KEYRING_USERNAME_KEY: Final[str] = "USERNAME"
KEYRING_PASSWORD_KEY: Final[str] = "PWD"

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
