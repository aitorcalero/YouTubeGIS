# YouTubeGIS

Este repositorio contiene un script que extrae títulos de vídeos de un canal de YouTube seleccionado, identifica localizaciones geográficas en esos títulos utilizando OpenAI, geocodifica esas localizaciones y, finalmente, las publica en ArcGIS Online como un FeatureService.

## Requisitos

- Python 3.x
- `googleapiclient`
- `openai`
- `arcgis`
- `keyring`
- `tabulate`
- `webbrowser`
- `pick`

## Funciones Principales
**get_api_keys(service_id)**
Obtiene las API keys almacenadas en el administrador de claves del sistema.

**extract_location_with_openai(title, api_key)**
Identifica posibles nombres de ubicaciones geográficas en un título utilizando OpenAI GPT-4.

**publish_geojson_as_feature_service(gis, filename)**
Publica un archivo GeoJSON en ArcGIS Online como un Feature Service.

**open_feature_service_in_browser(feature_service_id)**
Construye la URL del Feature Service publicado y la abre en el navegador predeterminado.

**save_to_geojson(features, filename)**
Guarda las características geocodificadas en un archivo GeoJSON.

**create_features_from_locations(titles, location_names, locations)**
Crea entidades geográficas (features) a partir de los títulos de los videos, los nombres de las ubicaciones identificadas y las ubicaciones geocodificadas.

**geocode_location(location_name)**
Geocodifica un nombre de ubicación utilizando el servicio de geocodificación de ArcGIS.

### Cuenta de ArcGIS Online

Es necesario tener una cuenta en ArcGIS Online para poder publicar y administrar el FeatureService. Si aún no tienes una, puedes [registrarte aquí](https://www.arcgis.com/home/signin.html).

### Configuración de `keyring`

El módulo `keyring` se utiliza para almacenar de forma segura las claves API y otros secretos. Para configurarlo:

1. Instala `keyring` con `pip install keyring`.
2. Desde tu terminal o consola, usa el siguiente comando para establecer una clave:

```bash
python -c "import keyring; keyring.set_password('YouTubeGIS', 'OPENAI_API_KEY', 'tu_clave_openai')"
