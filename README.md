# YouTubeGIS

`YouTubeGIS` extrae títulos de vídeos de un canal de YouTube, detecta ubicaciones geográficas en esos títulos con OpenAI, geocodifica esas ubicaciones con ArcGIS y publica el resultado como un `Feature Service` en ArcGIS Online.

## Estado actual

- El flujo principal está refactorizado para evitar efectos laterales al importar el módulo.
- La extracción mantiene alineados los títulos y las ubicaciones válidas para no publicar geometrías bajo el vídeo equivocado.
- La publicación a ArcGIS ya usa el flujo moderno basado en `Folder.add()`, compatible con la eliminación futura de `ContentManager.add`.

## Requisitos

- Python 3.11 o superior
- Una cuenta de ArcGIS Online con permisos para publicar contenido
- Clave API de OpenAI
- Clave API de YouTube Data v3

Dependencias Python:

- `arcgis`
- `google-api-python-client`
- `keyring`
- `openai`
- `pick`

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración de credenciales

El proyecto guarda secretos en el almacén seguro del sistema operativo mediante `keyring`.

Ejecuta:

```bash
python api_keys.py
```

El script pedirá:

- `OPENAI_API_KEY`
- `YOUTUBE_API_KEY`
- `USERNAME` de ArcGIS Online
- `PWD` de ArcGIS Online

## Ejecución

Desde la raíz del repositorio:

```bash
python YouTubeGIS.py
```

Si usas un entorno virtual local:

```bash
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
- [config.py](config.py) centraliza constantes y configuración.
- [validators.py](validators.py) valida entradas y parámetros.
- [exceptions.py](exceptions.py) define errores específicos del dominio.
- [test_YouTubeGIS.py](test_YouTubeGIS.py) cubre el flujo principal.
- [test_validators.py](test_validators.py) cubre la capa de validación.

## Funciones destacadas

`extract_location_with_openai(title, api_key)`
Extrae la localización más probable de un título usando OpenAI.

`extract_location_pairs_from_titles(titles, openai_api_key)`
Devuelve títulos y ubicaciones válidas preservando su alineación.

`create_features_from_locations(titles, location_names, locations)`
Crea `features` GeoJSON a partir de títulos y coordenadas geocodificadas.

`publish_geojson_as_feature_service(gis, filepath)`
Sube el GeoJSON a la carpeta raíz del usuario con `Folder.add()` y publica el item.

`process_and_publish_videos(youtube_api_key, openai_api_key, channel_id, num_videos)`
Ejecuta el flujo completo de extracción, geocodificación y publicación.

## Pruebas

Ejecuta la suite completa con:

```bash
python -m pytest
```

En la última verificación local, la suite pasó con `49` tests.

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
