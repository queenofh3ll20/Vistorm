
<div align="center">
<img width="250" alt="Preview" src="assets\images\vistorm_logo.jpg">
</div>
<h1 style="text-align: center;">Vistorm: Sound Impact on YouTube Shorts</h1>

## Descrizione del Progetto
---

**Vistorm** è un sistema avanzato per l’analisi e la previsione della viralità degli YouTube Shorts. Utilizzando dati in tempo reale e algoritmi di machine learning, permette di:

- Analizzare le tendenze musicali e il loro impatto sui video.
- Identificare le caratteristiche che rendono un contenuto virale.
- Ottimizzare le strategie di creazione di contenuti.

La piattaforma combina tecnologie all'avanguardia per trasformare intuizioni sui dati in risultati concreti.

## 🔧 Architettura Tecnica
---

<div align="center">
<img width="700" alt="Preview" src="assets\images\vistorm_pipeline.jpg">
</div>

### Pipeline di Elaborazione dei Dati

### Flusso della Pipeline

1. **Ingestione Dati:**
    
    - Raccoglie metriche video tramite **YouTube Data API** (es. visualizzazioni, like, commenti).
    - Utilizza **Audd Music Recognition API** per identificare tracce audio nei video.
    
2. **Streaming ed Elaborazione:**
	- Kafka invia i dati a Spark.
    - Applica tecniche di data processing tramite **Apache Spark**.
    - Arricchisce i dati con dataset Spotify tramite **Kaggle API**.
    - Effettua previsioni di successo video utilizzando modelli di machine learning sviluppati con **Spark MLlib**.
    
3. **Archiviazione e Visualizzazione:**
    
    - I dati predetti sono indicizzati in **Elasticsearch**.
    - I risultati sono presentati in dashboard interattive su **Kibana**.

## 🔑 Funzionalità Chiave
---
### 1. **Analisi dei Suoni**

Riconoscimento e classificazione automatica delle tracce audio nei video, con corrispondenza rispetto ai brani virali di Spotify.

### 2. **Modelli Predittivi**

Valutazione dell’impatto dei contenuti audio tramite:

- **Scenario senza musica:** Previsione del rendimento di un video senza tracce audio.
- **Scenario con musica non virale:** Valutazione dell'impatto ridotto sull'engagement dovuto all'utilizzo di brani meno popolari o poco riconosciuti.
- **Scenario con musica virale:** Stima dell’incremento di visibilità grazie all’utilizzo di brani di tendenza.

### 3. **Dashboard Interattive**

Visualizzazione intuitiva delle previsioni e dei trend tramite **Kibana**, con filtri e grafici personalizzati.

## 🎯 Cosa offre il progetto?
---
<div align="center">
<img width="700" alt="Preview" src="assets\images\vistorm.jpg">
</div>

Questo progetto si propone come uno strumento innovativo per _content creators_, offrendo loro la possibilità di comprendere l'impatto della musica sui loro video e monitorare il proprio canale.
Analizzando dati chiave e prevedendo il potenziale incremento di visibilità grazie all'uso di tracce virali, consente di ottimizzare le strategie di contenuto e massimizzare il coinvolgimento del pubblico.

<div align="center">
<img width="700" alt="Preview" src="assets\images\DASH1.png">
</div>
<div align="center">
<img width="700" alt="Preview" src="assets\images\DASH2.png">
</div>


## 📡 Stack Tecnologico
---

- **Data Ingestion:** Logstash.
- **Data Streaming**: Kafka.
- **Data Processing:** Apache Spark,.
- **Machine Learning:** Spark MLlib.
- **Indexing and Storage:** Elasticsearch.
- **Data Visualization:** Kibana.
- **Deployment:** Docker, Docker Compose.

## ⚙️ Requisiti
---
- Docker e Docker Compose installati. <a href="https://www.docker.com/" target="_blank" rel="noreferrer"> 
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original-wordmark.svg" alt="docker" width="40" height="40"/> 
</a>

- API Keys:
    - [YouTube Data API (Google APIs)](https://developers.google.com/youtube/v3?hl=it)
    -  [AudD Music Recognition API](https://audd.io/): 
    - [Top Spotify Songs Daily Updated (Kaggle APIs)](https://www.kaggle.com/datasets/asaniczka/top-spotify-songs-in-73-countries-daily-updated)

> [!important]  
> Utilizzando le API gratuite di Google, si dispone di un limite di **10.000 token giornalieri**. 
> Si consiglia di monitorare il consumo tramite il loro sistema di monitoring per evitare interruzioni.

## 🚀 Setup del Progetto
---
### 1. Clonare il Repository

```bash
git clone https://github.com/giulsp/Vistorm.git
```

### 2. Configurare le Variabili d'Ambiente

Creare un file `.env` nella directory `conf`:

```env
AUDD_API_KEY="your_api_key"
YT_API_KEY="your_api_key"
YT_CHANNEL_ID="channel_to_monitor"
```

Inserire il file `kaggle.json` con le credenziali nella directory `conf`.

### 3. Avviare i Servizi

Avviare l’intera pipeline tramite Docker Compose:

```bash
docker-compose up --build
```

### 4. Accesso alla Dashboard

La dashboard di Kibana è accessibile all'indirizzo:

```
http://localhost:5601
```

## 📂 Struttura della Repository
---

```plaintext
Vistorm/                  -> Directory principale del progetto
|
|-- conf/                -> Configurazioni e credenziali
|   |-- .env             -> File delle variabili di ambiente
|   |-- kaggle.json      -> Credenziali API di Kaggle
|   |-- logstash/        -> Configurazioni di Logstash
|       |-- logstash.conf -> File di configurazione principale
|       |-- sincedb      -> Stato della posizione di lettura di Logstash
|
|-- data/                -> Directory per la persistenza dei dati
|   |-- dataset/         -> Dataset per l'addestramento di SparkMLlib
|   |-- elasticsearch/   -> Indici e dati di Elasticsearch
|   |-- kaggle/          -> Dataset delle canzoni da Kaggle
|   |-- kibana/          -> (placeholder)
|   |-- Spark/           -> Modelli addestrati tramite SparkMLlib
|   |-- yt_out/          -> File NDJSON popolati in tempo reale dall'event listener
|
|-- docker_images/       -> Dockerfiles e requirements.txt per la costruzione delle immagini
|
|-- src/                 -> Script Python
|   |-- event_listener.py -> Monitoraggio nuovi caricamenti e preprocessing
|
|-- docker-compose.yml   -> File per avviare i container
```

## 🤝 Contribuire al Progetto
---
<div align="center">
<img width="700" alt="Preview" src="assets\images\contribute.jpg">
</div>

1. **Fork del Repository:** Creare una copia del progetto sul proprio account GitHub.
2. **Clonare il Repository Forkato:**

```bash
git clone https://github.com/giulsp/Vistorm.git
```

3. **Creare un Branch:**

```bash
git checkout -b nome-branch
```

4. **Effettuare le Modifiche:** Apportare i miglioramenti e testarli localmente.
5. **Commit e Push:**

```bash
git add .
git commit -m "Descrizione modifiche"
git push origin nome-branch
```

6. **Pull Request:** Aprire una pull request verso il repository originale.

## Credits

- ELK Stack: Copyright © Elasticsearch B.V. and licensed under the Elastic License 2.0.
- Apache Kafka & Apache Spark: Copyright © Apache Software Foundation, licensed under the Apache License 2.0.

## 📞 Contatti
---
Grazie per aver esplorato questo progetto! 
Spero che ti sia utile e che possa soddisfare le tue esigenze. 🚀

Per suggerimenti o problemi, contattami su GitHub: [queenofh3ll20](https://github.com/queenofh3ll20)
<div align="center" style="padding: 20px; border-radius: 16px; background: linear-gradient(145deg, #4e73df, #1c3faa); color: white; font-family: 'Segoe UI', sans-serif; box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2); max-width: 500px; margin: 30px auto; display: flex; align-items: center; gap: 20px;">
  <img src="assets\images\icon_giulia.jpg" alt="Profile Picture" width="90" style="border-radius: 50%; box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);">
  <div style="text-align: left;">
    <h2 style="margin: 0; font-size: 24px; font-weight: 600; color: #f0f8ff;">
      <a href="https://github.com/queenofh3ll20" target="_blank" style="color: #f0f8ff; text-decoration: none;">© Giulia Pulvirenti</a>
    </h2>
    <p style="margin: 5px 0 0; font-size: 15px; color: #dce7ff; font-weight: 500;">Computer Science Student</p>
  </div>
</div>
