from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from exceptions import ConfigurationError, ValidationError
from YouTubeGIS import (
    Credentials,
    build_feature_service_url,
    create_features_from_locations,
    extract_location_pairs_from_titles,
    extract_location_with_openai,
    get_root_folder,
    publish_geojson_as_feature_service,
    process_and_publish_videos,
)


@pytest.fixture
def mock_openai_response() -> MagicMock:
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Madrid, Spain"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


@patch("YouTubeGIS._import_openai_client_class")
def test_extract_location_with_openai_success(
    mock_import_openai: MagicMock,
    mock_openai_response: MagicMock,
) -> None:
    mock_openai_class = MagicMock()
    mock_client_instance = MagicMock()
    mock_import_openai.return_value = mock_openai_class
    mock_openai_class.return_value = mock_client_instance
    mock_client_instance.chat.completions.create.return_value = mock_openai_response

    result = extract_location_with_openai(
        "Visitando las calles de Madrid en 4K",
        "fake-api-key",
    )

    assert result == "Madrid, Spain"
    mock_client_instance.chat.completions.create.assert_called_once()


def test_extract_location_with_openai_no_key() -> None:
    with pytest.raises(ConfigurationError):
        extract_location_with_openai("Un video cualquiera", None)


@patch("YouTubeGIS.extract_location_with_openai")
def test_extract_location_pairs_from_titles_preserves_alignment(
    mock_extract_location: MagicMock,
) -> None:
    mock_extract_location.side_effect = ["Paris", None, "Tokyo"]

    matched_titles, location_names = extract_location_pairs_from_titles(
        ["Title 1", "Title 2 (No Location)", "Title 3"],
        "fake-api-key",
    )

    assert matched_titles == ["Title 1", "Title 3"]
    assert location_names == ["Paris", "Tokyo"]


def test_create_features_from_locations() -> None:
    titles = ["Title 1", "Title 3"]
    location_names = ["Paris", "Tokyo"]
    locations = [
        {"x": 2.3522, "y": 48.8566},
        {"x": 139.6917, "y": 35.6895},
    ]

    features = create_features_from_locations(titles, location_names, locations)

    assert len(features) == 2
    assert features[0]["properties"]["Title"] == "Title 1"
    assert features[0]["properties"]["Location"] == "Paris"
    assert features[0]["geometry"]["coordinates"] == [2.3522, 48.8566]
    assert features[1]["properties"]["Title"] == "Title 3"
    assert features[1]["properties"]["Location"] == "Tokyo"
    assert features[1]["geometry"]["coordinates"] == [139.6917, 35.6895]


def test_create_features_from_locations_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValidationError):
        create_features_from_locations(
            ["Title 1", "Title 2"],
            ["Paris"],
            [{"x": 2.3522, "y": 48.8566}],
        )


def test_build_feature_service_url_uses_dynamic_portal_url() -> None:
    url = build_feature_service_url(
        "abc123",
        "https://example.maps.arcgis.com/sharing/rest",
    )

    assert url == "https://example.maps.arcgis.com/home/item.html?id=abc123"


def test_get_root_folder_uses_logged_in_user() -> None:
    mock_gis = MagicMock()
    mock_user = MagicMock()
    mock_gis.users.me = mock_user
    mock_folder = MagicMock()
    mock_gis.content.folders.get.return_value = mock_folder

    result = get_root_folder(mock_gis)

    assert result is mock_folder
    mock_gis.content.folders.get.assert_called_once_with(owner=mock_user)


@patch("YouTubeGIS.get_root_folder")
@patch("YouTubeGIS._import_arcgis_content_types")
def test_publish_geojson_as_feature_service_uses_folder_add_job(
    mock_import_arcgis_content_types: MagicMock,
    mock_get_root_folder: MagicMock,
    tmp_path,
) -> None:
    filepath = tmp_path / "sample.geojson"
    filepath.write_text('{"type":"FeatureCollection","features":[{}]}', encoding="utf-8")

    mock_item_properties_class = MagicMock()
    mock_item_type_enum = MagicMock()
    mock_item_type_enum.GEOJSON = "GeoJson"
    mock_import_arcgis_content_types.return_value = (
        mock_item_properties_class,
        mock_item_type_enum,
    )

    mock_job = MagicMock()
    mock_item = MagicMock()
    mock_published_item = MagicMock()
    mock_published_item.id = "published-id"
    mock_job.result.return_value = mock_item
    mock_item.publish.return_value = mock_published_item

    mock_folder = MagicMock()
    mock_folder.add.return_value = mock_job
    mock_get_root_folder.return_value = mock_folder

    mock_gis = MagicMock()

    result = publish_geojson_as_feature_service(mock_gis, str(filepath))

    assert result is mock_published_item
    mock_item_properties_class.assert_called_once_with(
        title="sample",
        item_type="GeoJson",
        tags=["geojson", "featureservice"],
        file_name="sample.geojson",
    )
    mock_folder.add.assert_called_once_with(
        item_properties=mock_item_properties_class.return_value,
        file=str(filepath),
    )
    mock_job.result.assert_called_once_with()
    mock_item.publish.assert_called_once_with()


@patch("YouTubeGIS.open_feature_service_in_browser")
@patch("YouTubeGIS.publish_geojson_as_feature_service")
@patch("YouTubeGIS.save_to_geojson")
@patch("YouTubeGIS.create_features_from_locations")
@patch("YouTubeGIS.geocode_locations")
@patch("YouTubeGIS.extract_location_pairs_from_titles")
@patch("YouTubeGIS.get_youtube_videos")
@patch("YouTubeGIS.create_gis_connection")
def test_process_and_publish_videos_uses_aligned_titles(
    mock_create_gis_connection: MagicMock,
    mock_get_youtube_videos: MagicMock,
    mock_extract_pairs: MagicMock,
    mock_geocode_locations: MagicMock,
    mock_create_features: MagicMock,
    mock_save_to_geojson: MagicMock,
    mock_publish_geojson: MagicMock,
    mock_open_browser: MagicMock,
) -> None:
    credentials = Credentials(
        openai_api_key="openai-key",
        youtube_api_key="youtube-key",
        username="arcgis-user",
        password="arcgis-password",
    )
    mock_get_youtube_videos.return_value = ["Title 1", "Title 2", "Title 3"]
    mock_extract_pairs.return_value = (["Title 1", "Title 3"], ["Paris", "Tokyo"])
    mock_geocode_locations.return_value = [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]
    mock_create_features.return_value = [{"type": "Feature"}]
    mock_save_to_geojson.return_value = "output.geojson"

    mock_gis = MagicMock()
    mock_gis.url = "https://example.maps.arcgis.com/sharing/rest"
    mock_create_gis_connection.return_value = mock_gis

    published_item = MagicMock()
    published_item.id = "abc123"
    mock_publish_geojson.return_value = published_item

    result = process_and_publish_videos(
        "youtube-key",
        "openai-key",
        "UCabc123",
        10,
        arcgis_credentials=credentials,
    )

    assert result is published_item
    mock_create_features.assert_called_once_with(
        ["Title 1", "Title 3"],
        ["Paris", "Tokyo"],
        [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}],
    )
    mock_open_browser.assert_called_once_with(
        "abc123",
        portal_url="https://example.maps.arcgis.com",
    )
