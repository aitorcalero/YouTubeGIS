"""Unit tests for YouTubeGIS validators module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from exceptions import ValidationError, ConfigurationError
from validators import (
    validate_channel_id,
    validate_num_videos,
    validate_api_keys,
    validate_credentials,
    validate_location_name,
    validate_video_title,
    validate_features_list,
    validate_filename,
)


class TestChannelIDValidation:
    """Tests for YouTube channel ID validation."""

    def test_valid_channel_id(self) -> None:
        """Valid channel ID should pass validation."""
        validate_channel_id("UCdwdFOhBP9CoAOlHDTmTxaw")

    def test_invalid_channel_id_empty(self) -> None:
        """Empty channel ID should fail."""
        with pytest.raises(ValidationError):
            validate_channel_id("")

    def test_invalid_channel_id_too_short(self) -> None:
        """Channel ID shorter than 2 chars should fail."""
        with pytest.raises(ValidationError):
            validate_channel_id("U")

    def test_invalid_channel_id_wrong_prefix(self) -> None:
        """Channel ID not starting with 'UC' should fail."""
        with pytest.raises(ValidationError):
            validate_channel_id("ABdwdFOhBP9CoAOlHDTmTxaw")

    def test_invalid_channel_id_not_string(self) -> None:
        """Non-string channel ID should fail."""
        with pytest.raises(ValidationError):
            validate_channel_id(123)  # type: ignore


class TestNumVideosValidation:
    """Tests for number of videos validation."""

    def test_valid_num_videos_single(self) -> None:
        """Single video should be valid."""
        validate_num_videos(1)

    def test_valid_num_videos_multiple(self) -> None:
        """Multiple videos should be valid."""
        validate_num_videos(10)

    def test_valid_num_videos_max(self) -> None:
        """Max videos (100) should be valid."""
        validate_num_videos(100)

    def test_invalid_num_videos_zero(self) -> None:
        """Zero videos should fail."""
        with pytest.raises(ValidationError):
            validate_num_videos(0)

    def test_invalid_num_videos_negative(self) -> None:
        """Negative videos should fail."""
        with pytest.raises(ValidationError):
            validate_num_videos(-5)

    def test_invalid_num_videos_exceeds_max(self) -> None:
        """More than 100 videos should fail."""
        with pytest.raises(ValidationError):
            validate_num_videos(101)

    def test_invalid_num_videos_not_int(self) -> None:
        """Non-integer should fail."""
        with pytest.raises(ValidationError):
            validate_num_videos("10")  # type: ignore


class TestAPIKeysValidation:
    """Tests for API keys validation."""

    def test_valid_api_keys(self) -> None:
        """Valid API keys should pass."""
        validate_api_keys("sk-123456", "AIza123456")

    def test_missing_openai_key(self) -> None:
        """Missing OpenAI key should fail."""
        with pytest.raises(ConfigurationError):
            validate_api_keys(None, "AIza123456")

    def test_missing_youtube_key(self) -> None:
        """Missing YouTube key should fail."""
        with pytest.raises(ConfigurationError):
            validate_api_keys("sk-123456", None)

    def test_missing_all_keys(self) -> None:
        """Missing all keys should fail."""
        with pytest.raises(ConfigurationError):
            validate_api_keys(None, None)


class TestCredentialsValidation:
    """Tests for ArcGIS credentials validation."""

    def test_valid_credentials(self) -> None:
        """Valid credentials should pass."""
        validate_credentials("username", "password")

    def test_missing_username(self) -> None:
        """Missing username should fail."""
        with pytest.raises(ConfigurationError):
            validate_credentials(None, "password")

    def test_missing_password(self) -> None:
        """Missing password should fail."""
        with pytest.raises(ConfigurationError):
            validate_credentials("username", None)

    def test_missing_all_credentials(self) -> None:
        """Missing all credentials should fail."""
        with pytest.raises(ConfigurationError):
            validate_credentials(None, None)


class TestLocationNameValidation:
    """Tests for location name validation."""

    def test_valid_location_name(self) -> None:
        """Valid location name should pass."""
        validate_location_name("Madrid")

    def test_valid_location_name_with_spaces(self) -> None:
        """Location with spaces should be valid."""
        validate_location_name("Sierra de Guadarrama")

    def test_invalid_location_name_empty(self) -> None:
        """Empty location name should fail."""
        with pytest.raises(ValidationError):
            validate_location_name("")

    def test_invalid_location_name_too_short(self) -> None:
        """Location name with 1 char should fail."""
        with pytest.raises(ValidationError):
            validate_location_name("M")

    def test_invalid_location_name_none(self) -> None:
        """None location name should fail."""
        with pytest.raises(ValidationError):
            validate_location_name(None)  # type: ignore


class TestVideoTitleValidation:
    """Tests for video title validation."""

    def test_valid_video_title(self) -> None:
        """Valid video title should pass."""
        validate_video_title("Viajando por Madrid")

    def test_valid_video_title_long(self) -> None:
        """Long video title should be valid."""
        validate_video_title("Explorando las mejores ciudades del mundo")

    def test_invalid_video_title_empty(self) -> None:
        """Empty title should fail."""
        with pytest.raises(ValidationError):
            validate_video_title("")

    def test_invalid_video_title_none(self) -> None:
        """None title should fail."""
        with pytest.raises(ValidationError):
            validate_video_title(None)  # type: ignore

    def test_invalid_video_title_not_string(self) -> None:
        """Non-string title should fail."""
        with pytest.raises(ValidationError):
            validate_video_title(123)  # type: ignore


class TestFeaturesListValidation:
    """Tests for GeoJSON features list validation."""

    def test_valid_features_list(self) -> None:
        """Valid features list should pass."""
        validate_features_list([{"type": "Feature", "geometry": {}}])

    def test_valid_features_list_multiple(self) -> None:
        """Multiple features should be valid."""
        features = [{"type": "Feature"}, {"type": "Feature"}]
        validate_features_list(features)

    def test_invalid_features_not_list(self) -> None:
        """Non-list features should fail."""
        with pytest.raises(ValidationError):
            validate_features_list({"type": "Feature"})  # type: ignore

    def test_invalid_features_empty_list(self) -> None:
        """Empty features list should fail."""
        with pytest.raises(ValidationError):
            validate_features_list([])


class TestFilenameValidation:
    """Tests for output filename validation."""

    def test_valid_filename(self) -> None:
        """Valid filename should pass."""
        validate_filename("output_data.geojson")

    def test_valid_filename_with_path(self) -> None:
        """Filename with path should be valid."""
        validate_filename("path/to/output.geojson")

    def test_invalid_filename_wrong_extension(self) -> None:
        """Filename without .geojson extension should fail."""
        with pytest.raises(ValidationError):
            validate_filename("output.json")

    def test_invalid_filename_too_short(self) -> None:
        """Filename too short should fail."""
        with pytest.raises(ValidationError):
            validate_filename("a.geojson")

    def test_valid_filename_none(self) -> None:
        """None filename should pass (uses default)."""
        validate_filename(None)

    def test_invalid_filename_not_string(self) -> None:
        """Non-string filename should fail."""
        with pytest.raises(ValidationError):
            validate_filename(123)  # type: ignore
