# YouTubeGIS

Este repositorio contiene un script que extrae títulos de vídeos de un canal de YouTube, identifica localizaciones geográficas en esos títulos utilizando OpenAI, geocodifica esas localizaciones y, finalmente, las publica en ArcGIS Online como un FeatureService.

## Requisitos

- Python 3.x
- `googleapiclient`
- `openai`
- `arcgis`
- `keyring`
- `tabulate`
- `webbrowser`

## Cómo funciona

1. **Configuración del Logger**: Se utiliza el módulo `logging` para registrar y mostrar información y errores durante la ejecución del script.

2. **Obtener las API Keys**: Las claves API para YouTube y OpenAI se almacenan de forma segura utilizando `keyring`. 

3. **Extracción de Localizaciones con OpenAI**: Se utiliza la API de OpenAI para identificar nombres de lugares o localizaciones geográficas en los títulos de los vídeos.

4. **Geocodificación**: Una vez identificadas las localizaciones, se utilizan los servicios de geocodificación de ArcGIS para obtener sus coordenadas.

5. **Creación y Publicación de FeatureService**: Las localizaciones geocodificadas se guardan en un archivo GeoJSON, que luego se publica en ArcGIS Online como un FeatureService.

6. **Apertura del FeatureService en un Navegador**: Una vez publicado el FeatureService, el script automáticamente abre el servicio en un navegador para visualización.

## Cómo usar

1. Clona o descarga este repositorio.
2. Instala las bibliotecas necesarias utilizando `pip`.
3. Asegúrate de tener configurado `keyring` con las claves API necesarias.
4. Ejecuta el script.

## Contribuciones

Las contribuciones son bienvenidas. Si tienes sugerencias o mejoras, no dudes en abrir un issue o hacer un pull request.

## Licencia

[MIT](LICENSE)
