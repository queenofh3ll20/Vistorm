from pyspark.ml import PipelineModel
from pyspark.sql import SparkSession
from pyspark.sql.functions import hour,minute,second,year, month, dayofweek, col, exp, when, lit, udf, from_json, round
from pyspark.sql.types import StructType, StructField, StringType, IntegerType,FloatType,BooleanType
import json
import unicodedata


# Inizializza Spark
spark = SparkSession.builder.appName("UseModel_GBT").getOrCreate()

# Configura la lettura dal topic Kafka
kafka_server = "broker:9092"
topic_name = "yt_raw"

# Legge i dati dal topic Kafka, si collega al broker di kafka al topic selezionato e inizia a ricevere i messaggi
kafka_data = spark.readStream.format("kafka").option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", topic_name) \
    .option("startingOffsets", "latest") \
    .load()

# Decodifica i dati Kafka, li trasforma in un Data Frame utilizzabile da Spark
data = kafka_data.selectExpr("CAST(value AS STRING) as json_value")

# Definisce lo schema dei dati in ingresso da Kafka
json_schema = StructType([
    StructField("video_id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("description", StringType(), True),
    StructField("published_at", StringType(), True),
    StructField("channel_info", StructType([
        StructField("channel_id", StringType(), True),
        StructField("channel_name", StringType(), True),
        StructField("total_subscribers", StringType(), True),
        StructField("total_views", StringType(), True)
    ]), True),
    StructField("music_track", StructType([
        StructField("title", StringType(), True),
        StructField("artist", StringType(), True),
        StructField("album", StringType(), True),
        StructField("release_date", StringType(), True)
    ]), True)
])

data = data.select(from_json(col("json_value"), json_schema).alias("parsed_data"))

# Prende dall'intero data frame solo le colonne selezionate
data = data.select(
    col("parsed_data.video_id"),
    col("parsed_data.title"),
    col("parsed_data.description"),
    col("parsed_data.published_at"),
    col("parsed_data.channel_info.total_subscribers").alias("total_subscribers"),
    col("parsed_data.channel_info.total_views").alias("total_views"),
    col("parsed_data.music_track.title").alias("music_track_title"),
    col("parsed_data.music_track.artist").alias("music_track_artist"),
    year(col("parsed_data.published_at")).alias("year"),
    month(col("parsed_data.published_at")).alias("month"),
    dayofweek(col("parsed_data.published_at")).alias("day_of_week"),
    hour(col("parsed_data.published_at")).alias("hour"),
    minute(col("parsed_data.published_at")).alias("minute"),
    second(col("parsed_data.published_at")).alias("second")
)

# Conversione dei dati numerici (string -> integer)
data = data.withColumn("total_subscribers", col("total_subscribers").cast("integer"))
data = data.withColumn("total_views", col("total_views").cast("integer"))

# Carica il dataset delle canzoni (Schema Dataset Kaggle)
songs_schema = StructType([
    StructField("spotify_id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("artists", StringType(), True),
    StructField("daily_rank", IntegerType(), True),
    StructField("daily_movement", IntegerType(), True),
    StructField("weekly_movement", IntegerType(), True),
    StructField("country", StringType(), True),
    StructField("snapshot_date", StringType(), True),
    StructField("popularity", IntegerType(), True),
    StructField("is_explicit", BooleanType(), True),
    StructField("duration_ms", IntegerType(), True),
    StructField("album_name", StringType(), True),
    StructField("album_release_date", StringType(), True),
    StructField("danceability", FloatType(), True),
    StructField("energy", FloatType(), True),
    StructField("key", IntegerType(), True),
    StructField("loudness", FloatType(), True),
    StructField("mode", IntegerType(), True),
    StructField("speechiness", FloatType(), True),
    StructField("acousticness", FloatType(), True),
    StructField("instrumentalness", FloatType(), True),
    StructField("liveness", FloatType(), True),
    StructField("valence", FloatType(), True),
    StructField("tempo", FloatType(), True),
    StructField("time_signature", IntegerType(), True)
])

# Legge e decodifica il dataset di Kaggle
songs_raw = spark.read.text("data/kaggle/universal_top_spotify_songs.ndjson")
songs_dataset = songs_raw.select(from_json(col("value"), songs_schema).alias("data"))
songs_dataset = songs_dataset.select("data.*")

# ----------------- NORMALIZZAZIONE TITOLI ---------------------------------------------------------------
# UDF per normalizzare i caratteri speciali
def normalize_string(input_str):
    if input_str:
        return unicodedata.normalize('NFC', input_str)
    return input_str

normalize_string_udf = udf(normalize_string, StringType())

# Normalizza il dataset delle canzoni
songs_dataset_normalized = songs_dataset.withColumn(
    "title_normalized", normalize_string_udf(col("name"))
)

# Creazione delle liste normalizzate
titles_list_normalized = songs_dataset_normalized.select("title_normalized").rdd.map(lambda row: row["title_normalized"]).collect()

def extract_music_track_artist(music_track):
    try:
        track_info = json.loads(music_track)
        return track_info.get("artist", None)
    except (json.JSONDecodeError, TypeError):
        return None

extract_music_track_artist_udf = udf(extract_music_track_artist, StringType())

data = data.withColumn("music_track_title_normalized", normalize_string_udf(col("music_track_title")))
data = data.withColumn("music_track_artist_normalized", normalize_string_udf(col("music_track_artist")))
# ---------------------------------------------------------------------------------------------------------


# ------------------------------- PREDIZIONE --------------------------------------------------------------
# Carica i modelli salvati
print("Loading models...")
model_views = PipelineModel.load("data/Spark/model_views")
model_likes = PipelineModel.load("data/Spark/model_likes")
model_comments = PipelineModel.load("data/Spark/model_comments")


# Effettua le previsioni in tutti e 3 gli scenari: 0 (senza musica), 1 (con musica base), 2 (con musica virale)
data = data.withColumn("music_track", lit(0).cast("int"))
data = model_views.transform(data).withColumn("predicted_views_no_music", round(exp(col("prediction")) - 1).cast("int")) # formula per avere valori esatti e non negativi
data = data.drop("features")  # Rimuovi la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction", le rimuove ogni volta per effettuare una nuova predizione
data = model_likes.transform(data).withColumn("predicted_likes_no_music", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_comments.transform(data).withColumn("predicted_comments_no_music", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"

data = data.withColumn("music_track", lit(1).cast("int"))
data = model_views.transform(data).withColumn("predicted_views_music_base", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_likes.transform(data).withColumn("predicted_likes_music_base", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_comments.transform(data).withColumn("predicted_comments_music_base", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"

data = data.withColumn("music_track", lit(2).cast("int"))
data = model_views.transform(data).withColumn("predicted_views_music_top", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_likes.transform(data).withColumn("predicted_likes_music_top", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_comments.transform(data).withColumn("predicted_comments_music_top", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"

# Assegna a music_track la categoria del video (0 = senza musica, 1 = con musica non virale, 2 = con musica virale)
data = data.withColumn(
    "music_track",
    when(col("music_track_title_normalized").isNull() | col("music_track_artist_normalized").isNull(), lit(0))
    .when(
        (col("music_track_title_normalized").isin(titles_list_normalized)), lit(2) # confronta tra Youtube e Kaggle
    ).otherwise(lit(1))
)


# ------------------------------------------------ PREDIZIONE SCENARIO REALE ------------------------------------------------------------------
data = model_views.transform(data).withColumn("predicted_views_chosen", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_likes.transform(data).withColumn("predicted_likes_chosen", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"
data = model_comments.transform(data).withColumn("predicted_comments_chosen", round(exp(col("prediction")) - 1).cast("int"))
data = data.drop("features")  # Rimuovi di nuovo la colonna "features"
data = data.drop("prediction") # Rimuovi la colonna "prediction"

# Scrittura dei dati in stream verso Elasticsearch
query = data.writeStream \
    .outputMode("append") \
    .format("org.elasticsearch.spark.sql") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.resource", "youtube_data") \
    .option("checkpointLocation", "/tmp/checkpoint_es") \
    .start()

# Aspetta che il flusso di dati finisca
query.awaitTermination()