import kagglehub
import os
import pandas as pd
import json
import shutil

# Define the destination for the dataset file
destination_path = "/kaggle"
os.makedirs(destination_path, exist_ok=True)

# Download the dataset
path = kagglehub.dataset_download("asaniczka/top-spotify-songs-in-73-countries-daily-updated")
print("Path to dataset files:", path)

# Find the specific dataset file
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

# Move the dataset file to the destination
destination_file = os.path.join(destination_path, os.path.basename(dataset_file))
shutil.move(dataset_file, destination_file)
print(f"Dataset file moved to: {destination_file}")

# List of countries
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

# Convert the CSV to JSON, keeping only the specified countries
json_file = os.path.splitext(destination_file)[0] + ".ndjson"

try:
    # Read the CSV
    df = pd.read_csv(destination_file)
    
    # Filter the rows for the specified countries
    df_filtered = df[df['country'].isin(countries_to_include)]
    
    # Remove duplicates based on the 'Spotify_id' column
    df_filtered_no_duplicates = df_filtered.drop_duplicates(subset='spotify_id', keep='first')
    
    # Convert the filtered DataFrame to JSON
    df_filtered_no_duplicates.to_json(json_file, orient="records", lines=True)
    print(f"Dataset converted to JSON: {json_file}")
except Exception as e:
    print(f"Error converting CSV to JSON: {e}")
