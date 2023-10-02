import json
import logging
import os
import random
import string
import webbrowser
from datetime import datetime

import keyring
import openai
from arcgis.geocoding import geocode
from arcgis.gis import GIS
from googleapiclient.discovery import build
from pick import pick
from tabulate import tabulate

# Configuración del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.info(os.path.dirname(os.path.abspath(__file__)))

def get_api_keys(service_id):
# Leer API Keys desde un archivo
    openai_api_key = keyring.get_password(service_id, "OPENAI_API_KEY")
    youtube_api_key = keyring.get_password(service_id, "YOUTUBE_API_KEY")
    username = keyring.get_password(service_id, "USERNAME")
    pwd = keyring.get_password(service_id, "PWD")

    return openai_api_key,youtube_api_key,username,pwd

openai_api_key, youtube_api_key, username, pwd = get_api_keys("YouTubeGIS")

def extract_location_with_openai(title, api_key):
    """Extrae la localización geográfica más probable de un título usando OpenAI."""
    logging.info(f"Extrayendo localización del título: {title} usando OpenAI...")
    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en geografía. Necesito que me ayudes a extraer la localización y ubicaciones de algunas cadenas de texto que te voy a pasar"
                },
                {
                    "role": "user",
                    "content": f"Identifica y escribe solo el nombre de la localización geográfica en el título: {title}"
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        #logging.info(f"Response from OpenAI: {response}")
        
        assistant_messages = [msg for msg in response.get("messages", []) if msg["role"] == "assistant"]
        location_name = response.get("choices", [{}])[0].get("message", {}).get("content", None)

        return location_name.strip() if location_name else None
    except Exception as e:
        logging.error(f"Error while calling OpenAI API: {e}")
        return None


def generate_random_string(length):
    """Genera una cadena aleatoria del tamaño especificado con un timestamp adjunto."""
    
    # Obtener el timestamp actual y formatearlo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generar la cadena aleatoria
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(length))
    
    # Concatenar el timestamp y la cadena aleatoria y devolver
    return timestamp + "_" + random_string

def publish_geojson_as_feature_service(gis, filename):
    """Publica un archivo GeoJSON en ArcGIS como un FeatureService y devuelve el ítem publicado."""
    logging.info(f"Publicando el archivo {filename} en ArcGIS...")
    try:
        # Definir las propiedades del ítem
        item_properties = {
            "title": filename.split(".")[0],
            "type": "GeoJson",
            "tags": ["geojson", "featureservice"]
        }
        
        # Subir el archivo GeoJSON
        item = gis.content.add(item_properties, filename)
        
        # Publicar el archivo GeoJSON como un FeatureService
        published_item = item.publish()
        logging.info(f"GeoJSON published as FeatureService with ID: {published_item.id}")
        return published_item
    except Exception as e:
        logging.error(f"Error publishing GeoJSON: {e}")
        return None
  

def open_feature_service_in_browser(feature_service_id):
    """Construye la URL del FeatureService y la abre en el navegador predeterminado."""
    
    base_url = "https://geogeeks.maps.arcgis.com/home/item.html?id="
    full_url = f"{base_url}"+feature_service_id
    
    webbrowser.open(full_url, new=2)

def save_to_geojson(features, filename=generate_random_string(8)+".geojson"):
    """Guarda las características en un archivo GeoJSON."""
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(filename, 'w') as f:
        json.dump(geojson, f)
        
    logging.info(f"Arcchivo geojson correctamente generado en {filename}")
    
    return filename

def create_features_from_locations(titles, location_names, locations):
    features = []
    for title, location_name, location in zip(titles, location_names, locations):
        if location:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [location['x'], location['y']]
                },
                "properties": {
                    "Title": title,
                    "Location": location_name
                }
            }
            features.append(feature)
    return features

def geocode_location(location_name):
    """Geocodifica una localización y devuelve sus coordenadas."""
    logging.info(f"Geocodificando la localización: {location_name}...")
    try:
        geocoding_result = geocode(location_name, max_locations=1)
        if geocoding_result:
            return geocoding_result[0]['location']
        else:
            logging.warning(f"No geocoding result for location: {location_name}")
            return None
    except Exception as e:
        logging.error(f"Error geocoding location: {location_name}. Error: {e}")
        return None    
    
def geocode_locations(location_names):
    return [geocode_location(name) for name in location_names]

def extract_locations_from_titles(titles, openai_api_key):
    locations = []
    for title in titles:
        location_name = extract_location_with_openai(title, openai_api_key)
        if location_name:
            locations.append(location_name)
    return locations

def get_youtube_videos(youtube_api_key, channel_id, max_results):
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
    request = youtube.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=max_results,
        order='viewCount',
        type='video'
    )
    response = request.execute()
    return [item['snippet']['title'] for item in response['items']]

def process_and_publish_videos(youtube_api_key, openai_api_key, channel_id, num_videos):
    gis = GIS("https://www.arcgis.com", username, pwd)
    
    titles = get_youtube_videos(youtube_api_key, channel_id, num_videos)
    location_names = extract_locations_from_titles(titles, openai_api_key)
    locations = geocode_locations(location_names)
    features = create_features_from_locations(titles, location_names, locations)
    
    filename = save_to_geojson(features)
    
    open_feature_service_in_browser(publish_geojson_as_feature_service(gis, filename).id)

def yt_channel_selection():
    title = 'Elige el canal de YouTube que quieras: '
    channel_id = ["UCdwdFOhBP9CoAOlHDTmTxaw | Un Mundo Inmmenso", "UCknQM__AyaqSdxunkqpavDg | Misias pero Viajeras","UCRTq5KxoyKuquatzn2iF0Pg | Military Lab","UCmmPgObSUPw1HL2lq6H4ffA | GeographyNow"]
    option, index = pick(channel_id, title, " 👉 ")
    return option.split("|")[0].strip()

def num_videos():
    title = 'Dime cuántos vídeos quieres procesar: '
    channel_id = ["1", "5","10","15", "20", "50"]
    option, index = pick(channel_id, title," 👉 ")
    return option



# Ejecución
def main():
    process_and_publish_videos(youtube_api_key, openai_api_key, yt_channel_selection(), int(num_videos()))

if __name__ == '__main__':
    main()