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

### Cuenta de ArcGIS Online

Es necesario tener una cuenta en ArcGIS Online para poder publicar y administrar el FeatureService. Si aún no tienes una, puedes [registrarte aquí](https://www.arcgis.com/home/signin.html).

### Configuración de `keyring`

El módulo `keyring` se utiliza para almacenar de forma segura las claves API y otros secretos. Para configurarlo:

1. Instala `keyring` con `pip install keyring`.
2. Desde tu terminal o consola, usa el siguiente comando para establecer una clave:

```bash
python -c "import keyring; keyring.set_password('YouTubeGIS', 'OPENAI_API_KEY', 'tu_clave_openai')"
