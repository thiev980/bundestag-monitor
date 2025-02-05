import json
import os
from transformers import pipeline
import pandas as pd

# Sentiment-Analyse-Modell laden
sentiment_model = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Pfad zu den JSON-Dateien
json_dir = "data/json"
results = []

# Sentiment für jede Sitzung berechnen
for json_file in sorted(os.listdir(json_dir)):
    if json_file.endswith(".json"):
        with open(os.path.join(json_dir, json_file), "r", encoding="utf-8") as f:
            data = json.load(f)
            session_number = data["sitzungsnummer"]
            text = data["text"]

            # Kürzen auf max. 512 Tokens (BERT-Limitation)
            text_snippet = text[:512]

            # Sentiment berechnen
            sentiment_result = sentiment_model(text_snippet)
            sentiment = sentiment_result[0]["label"]

            results.append({"Sitzungsnummer": session_number, "Sentiment": sentiment})

# Ergebnisse in Tabelle anzeigen
df_sentiment = pd.DataFrame(results)
tools.display_dataframe_to_user(name="Sentiment-Analyse der Sitzungen", dataframe=df_sentiment)