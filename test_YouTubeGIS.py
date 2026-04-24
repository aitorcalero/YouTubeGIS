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
    load_credentials,
    load_credentials_from_environment,
    main,
    merge_credentials,
    parse_args,
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
    called_kwargs = mock_client_instance.chat.completions.create.call_args.kwargs
    assert called_kwargs["messages"][0]["content"].startswith(
        "Eres un experto en geografía y análisis de títulos de vídeo."
    )
    assert "una única localización geográfica real" in called_kwargs["messages"][1]["content"]


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


@patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "env-openai",
        "YOUTUBE_API_KEY": "env-youtube",
        "ARCGIS_USERNAME": "env-user",
        "ARCGIS_PASSWORD": "env-password",
    },
    clear=True,
)
def test_load_credentials_from_environment_supports_all_values() -> None:
    credentials = load_credentials_from_environment()

    assert credentials == Credentials(
        openai_api_key="env-openai",
        youtube_api_key="env-youtube",
        username="env-user",
        password="env-password",
    )


def test_merge_credentials_prefers_primary_values() -> None:
    merged = merge_credentials(
        Credentials("keyring-openai", None, "keyring-user", None),
        Credentials("env-openai", "env-youtube", "env-user", "env-password"),
    )

    assert merged == Credentials(
        openai_api_key="keyring-openai",
        youtube_api_key="env-youtube",
        username="keyring-user",
        password="env-password",
    )


def test_parse_args_accepts_channel_id_and_num_videos() -> None:
    args = parse_args(["--channel-id", "UCabc123", "--num-videos", "12"])

    assert args.channel_id == "UCabc123"
    assert args.num_videos == 12


def test_parse_args_accepts_dry_run_flag() -> None:
    args = parse_args(["--dry-run"])

    assert args.dry_run is True


@patch("YouTubeGIS.process_and_publish_videos")
@patch("YouTubeGIS.load_credentials")
def test_main_uses_cli_arguments_without_interactive_selection(
    mock_load_credentials: MagicMock,
    mock_process_and_publish_videos: MagicMock,
) -> None:
    credentials = Credentials(
        openai_api_key="openai-key",
        youtube_api_key="youtube-key",
        username="arcgis-user",
        password="arcgis-password",
    )
    mock_load_credentials.return_value = credentials

    main(["--channel-id", "UCabc123", "--num-videos", "12"])

    mock_process_and_publish_videos.assert_called_once_with(
        "youtube-key",
        "openai-key",
        "UCabc123",
        12,
        arcgis_credentials=credentials,
        open_browser=True,
        dry_run=False,
    )


@patch("YouTubeGIS.process_and_publish_videos")
@patch("YouTubeGIS.load_credentials")
def test_main_passes_dry_run_flag(
    mock_load_credentials: MagicMock,
    mock_process_and_publish_videos: MagicMock,
) -> None:
    credentials = Credentials(
        openai_api_key="openai-key",
        youtube_api_key="youtube-key",
        username="arcgis-user",
        password="arcgis-password",
    )
    mock_load_credentials.return_value = credentials

    main(["--channel-id", "UCabc123", "--num-videos", "12", "--dry-run"])

    mock_process_and_publish_videos.assert_called_once_with(
        "youtube-key",
        "openai-key",
        "UCabc123",
        12,
        arcgis_credentials=credentials,
        open_browser=True,
        dry_run=True,
    )


@patch("YouTubeGIS.webbrowser.open")
def test_main_with_no_browser_does_not_open_browser(mock_webbrowser_open: MagicMock) -> None:
    with patch("YouTubeGIS._resolve_credentials_from_args") as mock_resolve, patch(
        "YouTubeGIS.process_and_publish_videos"
    ) as mock_process:
        credentials = Credentials(
            openai_api_key="openai-key",
            youtube_api_key="youtube-key",
            username="arcgis-user",
            password="arcgis-password",
        )
        mock_resolve.return_value = credentials

        main([
            "--channel-id",
            "UCabc123",
            "--num-videos",
            "1",
            "--no-browser",
        ])

        mock_process.assert_called_once()
        kwargs = mock_process.call_args.kwargs
        assert kwargs["open_browser"] is False
        mock_webbrowser_open.assert_not_called()


@patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "env-openai",
        "ARCGIS_PASSWORD": "env-password",
    },
    clear=True,
)
@patch("YouTubeGIS._load_keyring_credentials")
def test_load_credentials_combines_keyring_and_environment(
    mock_load_keyring_credentials: MagicMock,
) -> None:
    mock_load_keyring_credentials.return_value = Credentials(
        openai_api_key=None,
        youtube_api_key="keyring-youtube",
        username="keyring-user",
        password=None,
    )

    credentials = load_credentials()

    assert credentials == Credentials(
        openai_api_key="env-openai",
        youtube_api_key="keyring-youtube",
        username="keyring-user",
        password="env-password",
    )


@patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "env-openai",
        "YOUTUBE_API_KEY": "env-youtube",
        "ARCGIS_USERNAME": "env-user",
        "ARCGIS_PASSWORD": "env-password",
    },
    clear=True,
)
@patch("YouTubeGIS._load_keyring_credentials", side_effect=ConfigurationError("missing keyring"))
def test_load_credentials_uses_environment_when_keyring_unavailable(
    mock_load_keyring_credentials: MagicMock,
) -> None:
    credentials = load_credentials()

    assert credentials == Credentials(
        openai_api_key="env-openai",
        youtube_api_key="env-youtube",
        username="env-user",
        password="env-password",
    )
    mock_load_keyring_credentials.assert_called_once()


@patch.dict(
    "os.environ",
    {
        "OPENAI_API_KEY": "env-openai",
        "YOUTUBE_API_KEY": "env-youtube",
        "ARCGIS_USERNAME": "env-user",
        "ARCGIS_PASSWORD": "env-password",
    },
    clear=True,
)
@patch("YouTubeGIS._load_keyring_credentials", side_effect=RuntimeError("NoKeyringError"))
def test_load_credentials_uses_environment_when_keyring_raises_runtime_error(
    mock_load_keyring_credentials: MagicMock,
) -> None:
    credentials = load_credentials()

    assert credentials == Credentials(
        openai_api_key="env-openai",
        youtube_api_key="env-youtube",
        username="env-user",
        password="env-password",
    )
    mock_load_keyring_credentials.assert_called_once()


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
def test_process_and_publish_videos_dry_run_skips_publication_and_browser(
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
    mock_get_youtube_videos.return_value = ["Title 1"]
    mock_extract_pairs.return_value = (["Title 1"], ["Madrid"])
    mock_geocode_locations.return_value = [{"x": 1.0, "y": 2.0}]
    mock_create_features.return_value = [{"type": "Feature"}]
    mock_save_to_geojson.return_value = "output.geojson"

    mock_gis = MagicMock()
    mock_create_gis_connection.return_value = mock_gis

    result = process_and_publish_videos(
        "youtube-key",
        "openai-key",
        "UCabc123",
        10,
        arcgis_credentials=credentials,
        dry_run=True,
    )

    assert result == "output.geojson"
    mock_publish_geojson.assert_not_called()
    mock_open_browser.assert_not_called()


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
