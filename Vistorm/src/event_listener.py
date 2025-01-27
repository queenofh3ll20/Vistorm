import time
import requests
import json
import os
from datetime import datetime, timezone
import yt_dlp
from pydub import AudioSegment
import io

# Configurazione API
YOUTUBE_API_KEY = os.getenv("YT_API_KEY")  # Chiave API di YouTube
AUDD_API_KEY = os.getenv("AUDD_API_KEY")  # Chiave API di Audd.io
CHANNEL_ID = os.getenv("YT_CHANNEL_ID")  # ID del canale YouTube
OUTPUT_FILE = "data/yt_out/yt_data.ndjson"  # File per salvare i dati
POLL_INTERVAL = 30  # Intervallo di polling in secondi, ogni 30sec chiede a Youtube se sono stati caricati video

# Timestamp di avvio
script_start_time = datetime.now(timezone.utc)

# Memorizza l'ID dell'ultimo video controllato
last_video_id = None

# ----------------------- CANALE -----------------------
# Funzione per ottenere informazioni sul canale
def get_channel_info(channel_id, api_key):
    """Ottieni informazioni sul canale YouTube."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics",
        "id": channel_id,
        "key": api_key,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    # Restituisce le informazioni presenti in data
    if "items" in data and len(data["items"]) > 0:
        channel = data["items"][0]
        return {
            "channel_id": channel_id,
            "channel_name": channel["snippet"]["title"],
            "total_subscribers": int(channel["statistics"].get("subscriberCount", 0)),
            "total_views": int(channel["statistics"].get("viewCount", 0)),
        }
    return None

# ----------------------- VIDEO -----------------------
# Funzione per ottenere l'ultimo video caricato su un canale
def get_latest_video(channel_id, api_key):
    """Ottieni l'ultimo video caricato su un canale."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 1,
        "order": "date",
        "type": "video",
        "key": api_key,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        video = data["items"][0]
        video_id = video["id"]["videoId"]
        video_title = video["snippet"]["title"]
        video_description = video["snippet"]["description"]
        video_published = video["snippet"]["publishedAt"]

        # Converte la data di pubblicazione in un oggetto datetime
        published_at = datetime.fromisoformat(video_published.replace("Z", "+00:00"))

        return {
            "video_id": video_id,
            "title": video_title,
            "description": video_description,
            "published_at": published_at,
        }
    return None

# Funzione per verificare se un video è uno Shorts
def is_youtube_short(video_id, api_key):
    """Verifica se il video è uno Shorts (durata inferiore a 60 secondi)."""
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "contentDetails",
        "id": video_id,
        "key": api_key,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        duration = data["items"][0]["contentDetails"]["duration"]

        # Converte la durata ISO 8601 in secondi
        time_str = duration.replace("PT", "").replace("M", ":").replace("S", "")
        if ":" in time_str:
            minutes, seconds = map(int, time_str.split(":"))
            total_seconds = minutes * 60 + seconds
        else:
            total_seconds = int(time_str)

        return total_seconds <= 60
    return False

# Funzione per riconoscere musica da un video YouTube (ESTRAZIONE -> AUDD)
def recognize_music_from_youtube(url):
    """Riconosci musica da un video YouTube."""
    try:
        audio_path = '/tmp/audio.webm'

        if os.path.exists(audio_path):
            os.remove(audio_path)  # Rimuovi il file esistente prima del download

        print("Inizio riconoscimento musicale...")  # Debug

        # Usa yt-dlp per scaricare solo l'audio senza conversione
        ydl_opts = {
            'format': 'bestaudio/best',  # Scarica solo l'audio migliore disponibile
            'outtmpl': '/tmp/audio.%(ext)s',  # Salva l'audio in /tmp/audio.mp3
            'quiet': False,  # Mostra i dettagli del download
            'nocheck': True, 
        }

        # Scarica l'audio dal video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            audio_path = '/tmp/audio.webm'  # Percorso del file audio scaricato

        # Controlla se il file è stato scaricato correttamente
        if not os.path.exists(audio_path):
            print(f"Errore: il file audio non è stato trovato in {audio_path}")
            return None

        # Carica l'audio in memoria
        print("Preparazione snippet audio...")
        audio = AudioSegment.from_file(audio_path)
        snippet = audio[:30000]  # 30 seconds snippet
        snippet_buffer = io.BytesIO()
        snippet.export(snippet_buffer, format="mp3")
        snippet_buffer.seek(0)

        # Invia lo snippet all'API di Audd.io
        print("Invio snippet all'API di Audd.io...")
        data = {
            'api_token': AUDD_API_KEY,
            'return': 'apple_music,spotify',  # Include le fonti di musica
        }
        files = {
            'file': ('audio.mp3', snippet_buffer, 'audio/mpeg')
        }

        response = requests.post("https://api.audd.io/", data=data, files=files)
        print(f"Risposta API Audd.io: {response.status_code} - {response.text}")
        response.raise_for_status() 

        result = response.json()
        if result.get("status") == "success" and result.get("result"):
            track_info = result["result"]
            return {
                "title": track_info.get("title"),
                "artist": track_info.get("artist"),
                "album": track_info.get("album"),
                "release_date": track_info.get("release_date"),
            }
        else:
            print("Nessuna traccia musicale riconosciuta.")
            return False
    except requests.exceptions.HTTPError as http_err:
        print(f"Errore HTTP: {http_err}")
        return None
    except Exception as e:
        print(f"Errore nel riconoscimento musicale: {e}")
        return None

# Funzione per salvare i dati in un file JSON
def save_data_to_json(video_data, music_data, channel_data, output_file):
    """Salva i dati del video, della traccia musicale e del canale in un file JSON."""
    combined_data = {
        "video_id": video_data["video_id"],
        "title": video_data["title"],
        "description": video_data["description"],
        "published_at": video_data["published_at"].isoformat(),
        "channel_info": channel_data,
        "music_track": music_data,
    }

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(combined_data) + "\n")

# Main script
if __name__ == "__main__":
    print(f"Script avviato alle {script_start_time}.")

    # Ottiene informazioni sul canale
    channel_info = get_channel_info(CHANNEL_ID, YOUTUBE_API_KEY)
    if not channel_info:
        print("Errore nel recupero delle informazioni del canale.")
        exit(1)

    print(f"Monitorando il canale: {channel_info['channel_name']} ({channel_info['channel_id']})")

    while True:
        try:
            # Ottiene l'ultimo video caricato
            video = get_latest_video(CHANNEL_ID, YOUTUBE_API_KEY)
            if video:
                # Controlla se il video è stato pubblicato dopo l'avvio dello script
                if video["published_at"] > script_start_time:
                    if video["video_id"] != last_video_id:
                        last_video_id = video["video_id"]

                        # Verifica se è uno Shorts
                        if is_youtube_short(video["video_id"], YOUTUBE_API_KEY):
                            print(f"Nuovo Shorts trovato: {video['title']} ({video['video_id']})")

                            # Riconosce la musica
                            music_info = recognize_music_from_youtube(
                                f"https://www.youtube.com/watch?v={video['video_id']}"
                            )
                            print("Risultato del riconoscimento musicale:", music_info)

                            # Salva i dati del video, della musica e del canale
                            save_data_to_json(video, music_info, channel_info, OUTPUT_FILE)
                            print(f"Dati salvati in {OUTPUT_FILE}.")
                        else:
                            print(f"Ignorato: {video['title']} non è uno Shorts.")
                            print("Monitorando il canale in attesa di nuovi video...")
                    else: print("Monitorando il canale in attesa di nuovi video...")
                else:
                    print("Monitorando il canale in attesa di nuovi video...")

        except Exception as e:
            print(f"Errore durante il controllo: {e}")

        # Attende prima di controllare nuovamente
        time.sleep(POLL_INTERVAL)
