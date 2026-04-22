# YouTubeGIS

`YouTubeGIS` transforma títulos de vídeos de YouTube en datos geoespaciales: detecta ubicaciones con OpenAI, las geocodifica con ArcGIS y publica el resultado como un `Feature Service` en ArcGIS Online.

## Estado actual

- El flujo principal está refactorizado para evitar efectos laterales al importar el módulo.
- La extracción mantiene alineados los títulos y las ubicaciones válidas para no publicar geometrías bajo el vídeo equivocado.
- La publicación a ArcGIS ya usa el flujo moderno basado en `Folder.add()`, compatible con la eliminación futura de `ContentManager.add`.
- El proyecto incluye un asistente real de configuración de credenciales (`api_keys.py`) y soporte de fallback con variables de entorno.

## Requisitos

- Python 3.11 o superior
- Una cuenta de ArcGIS Online con permisos para publicar contenido
- Clave API de OpenAI
- Clave API de YouTube Data v3

Dependencias Python principales:

- `arcgis`
- `google-api-python-client`
- `keyring`
- `openai`
- `pick`
- `pytest`

## Instalación

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración de credenciales

El proyecto admite dos formas de resolver secretos:

1. **`keyring`** como mecanismo principal recomendado
2. **Variables de entorno** como fallback, útil para servidores, CI/CD o ejecuciones automatizadas

### Opción recomendada: asistente interactivo

Ejecuta:

```bash
python api_keys.py
```

El asistente solicitará y guardará en `keyring`:

- `OPENAI_API_KEY`
- `YOUTUBE_API_KEY`
- `USERNAME` de ArcGIS Online
- `PWD` de ArcGIS Online

Si ya existen valores guardados, el asistente preguntará si quieres sobrescribirlos.

### Opción alternativa: variables de entorno

Si una credencial no existe en `keyring`, `YouTubeGIS` intentará resolverla desde estas variables:

- `OPENAI_API_KEY`
- `YOUTUBE_API_KEY`
- `ARCGIS_USERNAME`
- `ARCGIS_PASSWORD`

#### Ejemplo en PowerShell

```powershell
$env:OPENAI_API_KEY="tu-clave-openai"
$env:YOUTUBE_API_KEY="tu-clave-youtube"
$env:ARCGIS_USERNAME="tu-usuario"
$env:ARCGIS_PASSWORD="tu-password"
python .\YouTubeGIS.py
```

#### Ejemplo en Bash

```bash
export OPENAI_API_KEY="tu-clave-openai"
export YOUTUBE_API_KEY="tu-clave-youtube"
export ARCGIS_USERNAME="tu-usuario"
export ARCGIS_PASSWORD="tu-password"
python YouTubeGIS.py
```

## Ejecución

Desde la raíz del repositorio:

```bash
python YouTubeGIS.py
```

Si usas un entorno virtual local en Windows:

```powershell
.\.venv\Scripts\python.exe .\YouTubeGIS.py
```

El script te permitirá:

- elegir un canal de YouTube preconfigurado
- elegir cuántos vídeos procesar
- publicar el GeoJSON generado como `Feature Service`
- abrir el item publicado en tu navegador

Los archivos GeoJSON intermedios se generan en `output/`.

## Estructura principal

- [YouTubeGIS.py](YouTubeGIS.py) contiene el flujo principal.
- [api_keys.py](api_keys.py) ofrece el asistente interactivo para configurar credenciales.
- [config.py](config.py) centraliza constantes, claves de `keyring` y nombres de variables de entorno.
- [validators.py](validators.py) valida entradas y parámetros.
- [exceptions.py](exceptions.py) define errores específicos del dominio.
- [test_YouTubeGIS.py](test_YouTubeGIS.py) cubre el flujo principal.
- [test_validators.py](test_validators.py) cubre la capa de validación.
- [test_api_keys.py](test_api_keys.py) cubre el asistente de configuración.

## Funciones destacadas

### `load_credentials(service_id=KEYRING_SERVICE_ID)`
Carga credenciales desde `keyring` y completa cualquier valor ausente con variables de entorno.

### `load_credentials_from_environment()`
Resuelve credenciales directamente desde el entorno para ejecuciones no interactivas.

### `extract_location_with_openai(title, api_key)`
Extrae la localización más probable de un título usando OpenAI.

### `extract_location_pairs_from_titles(titles, openai_api_key)`
Devuelve títulos y ubicaciones válidas preservando su alineación.

### `create_features_from_locations(titles, location_names, locations)`
Crea `features` GeoJSON a partir de títulos y coordenadas geocodificadas.

### `publish_geojson_as_feature_service(gis, filepath)`
Sube el GeoJSON a la carpeta raíz del usuario con `Folder.add()` y publica el item.

### `process_and_publish_videos(youtube_api_key, openai_api_key, channel_id, num_videos)`
Ejecuta el flujo completo de extracción, geocodificación y publicación.

## Pruebas

Ejecuta la suite completa con:

```bash
python -m pytest
```

La suite cubre tanto el flujo principal como la configuración de credenciales y la validación de entradas.

## Notas sobre ArcGIS API for Python

La documentación oficial de Esri sigue publicando la serie `2.4.x` como versión actual a fecha de `22 de abril de 2026`, pero `ContentManager.add` ya está deprecado desde `2.3.0` y previsto para eliminación en `3.0.0`. Por eso este repositorio ya usa el patrón:

```python
folder = gis.content.folders.get(owner=gis.users.me)
job = folder.add(item_properties=item_properties, file=filepath)
item = job.result()
published_item = item.publish()
```

## Limitaciones

- La detección de ubicaciones depende de la calidad del título del vídeo.
- La geocodificación usa el mejor resultado disponible y puede requerir revisión manual en casos ambiguos.
- La publicación real depende de que la cuenta ArcGIS tenga permisos y cuota disponibles.
- El fallback por variables de entorno está pensado para ejecución no interactiva; para escritorio, `keyring` sigue siendo la opción más cómoda.
