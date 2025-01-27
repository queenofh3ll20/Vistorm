from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml import Pipeline
from pyspark.sql.functions import year, month, dayofweek, log, exp

# Inizializza Spark
spark = SparkSession.builder.appName("TrainModel_GBT").getOrCreate()

# Carica il dataset di training (in formato JSON)
data = spark.read.json("data/dataset/dataset.ndjson")

# Estrae le informazioni dai dati
data = data.withColumn("total_subscribers", data["channel_info.total_subscribers"])

# Trasforma 'published_at' in variabili temporali
data = data.withColumn("year", year(data["published_at"]))
data = data.withColumn("month", month(data["published_at"]))
data = data.withColumn("day_of_week", dayofweek(data["published_at"]))

# Trasforma i target (video_nviews, video_nlikes, video_ncomments) in logaritmi altrimenti potrebbe fare predizioni negative
data = data.withColumn("log_video_nviews", log(data["video_nviews"] + 1))
data = data.withColumn("log_video_nlikes", log(data["video_nlikes"] + 1))
data = data.withColumn("log_video_ncomments", log(data["video_ncomments"] + 1))

# Prepara le feature per il modello, quindi i dati che il modello utilizzerà per le predizioni
feature_columns = ["total_subscribers", "year", "month", "day_of_week", "music_track"]
assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")

# Crea i modelli GBT per i tre target 
rf_views = GBTRegressor(featuresCol="features", labelCol="log_video_nviews", maxIter=100)
rf_likes = GBTRegressor(featuresCol="features", labelCol="log_video_nlikes", maxIter=100)
rf_comments = GBTRegressor(featuresCol="features", labelCol="log_video_ncomments", maxIter=100)

# Crea le pipeline per ciascun target
pipeline_views = Pipeline(stages=[assembler, rf_views])
pipeline_likes = Pipeline(stages=[assembler, rf_likes])
pipeline_comments = Pipeline(stages=[assembler, rf_comments])

# Addestra i modelli
model_views = pipeline_views.fit(data)
model_likes = pipeline_likes.fit(data)
model_comments = pipeline_comments.fit(data)

# Salva i modelli
model_views.save("data/Spark/model_views")
model_likes.save("data/Spark/model_likes")
model_comments.save("data/Spark/model_comments")


# ------------------------------------- TEST -------------------------------------
# Previsioni con la trasformazione inversa (esponenziale)
predictions_views = model_views.transform(data)
predictions_likes = model_likes.transform(data)
predictions_comments = model_comments.transform(data)

# Applica la trasformazione inversa (esponenziale) per ottenere i valori originali
predictions_views = predictions_views.withColumn("predicted_views", exp(predictions_views["prediction"]) - 1)
predictions_likes = predictions_likes.withColumn("predicted_likes", exp(predictions_likes["prediction"]) - 1)
predictions_comments = predictions_comments.withColumn("predicted_comments", exp(predictions_comments["prediction"]) - 1)

# Mostra le previsioni finali
predictions_views.select("video_id", "predicted_views").show()
predictions_likes.select("video_id", "predicted_likes").show()
predictions_comments.select("video_id", "predicted_comments").show()
# ---------------------------------------------------------------------------------

# Ferma Spark
spark.stop()
