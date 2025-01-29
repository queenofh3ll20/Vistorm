import kagglehub
import os
import pandas as pd
import json
import shutil
from datetime import datetime, timedelta

# Definisce la destinazione per il file dataset
destination_path = "/kaggle"
os.makedirs(destination_path, exist_ok=True)

# Scarica il dataset
path = kagglehub.dataset_download("asaniczka/top-spotify-songs-in-73-countries-daily-updated")
print("Path to dataset files:", path)

# Trova il file dataset
dataset_file = None
for root, _, files in os.walk(path):
    for file in files:
        if file.endswith(".csv"):
            dataset_file = os.path.join(root, file)
            break
    if dataset_file:
        break

if not dataset_file:
    print("No dataset.csv file found!")
    exit()

# Sposta il file alla destinazione
destination_file = os.path.join(destination_path, os.path.basename(dataset_file))
shutil.move(dataset_file, destination_file)
print(f"Dataset file moved to: {destination_file}")

# Lista dei Countries
countries_to_include = [
    # Nord America
    "CA", "US", "MX",

    # Caraibi
    "AG", "BS", "BB", "CU", "DM", "GD", "JM", "HT", "DO", "KN", "LC", "VC", "TT", "PR",

    # America Centrale
    "BZ", "CR", "SV", "GT", "HN", "NI", "PA",

    # Sud America
    "AR", "BR", "CL", "CO", "PE", "UY", "VE",

    # Europa
    "AL", "AD", "AM", "AT", "AZ", "BY", "BE", "BA", "BG", "HR", "CY", "DK", "EE", "FI", "FR", "GE", "DE", "GR", "IE", "IS", "IT", "XK", "LV", "LI", "LT", "LU", "MT", "MD", "MC", "ME", "NL", "PL", "PT", "GB", "CZ", "RO", "SM", "RS", "SK", "SI", "ES", "SE", "CH", "UA",

    # Oceania
    "AU", "NZ"
]

# Data di oggi
today_date = datetime.today().strftime('%Y-%m-%d')
yesterday_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')


# Converte il CSV a JSON, mantenendo solo i paesi selezionati
json_file = os.path.splitext(destination_file)[0] + ".ndjson"

try:
    # Legge il CSV
    df = pd.read_csv(destination_file)
    
    # Filtra le righe per paesi
    df_filtered = df[df['country'].isin(countries_to_include)]

    # Filtra per data (mantieni solo la data odierna)
    df_filtered_recent = df_filtered[df_filtered['snapshot_date'].isin([today_date, yesterday_date])]
    
    # Rimuove i duplicati basati sulla colonn 'spotify_id'
    df_filtered_no_duplicates = df_filtered_recent.drop_duplicates(subset='spotify_id', keep='first')
    
    # Converte il DataFrame filtrato a JSON
    df_filtered_no_duplicates.to_json(json_file, orient="records", lines=True)
    print(f"Dataset converted to JSON: {json_file}")
except Exception as e:
    print(f"Error converting CSV to JSON: {e}")
