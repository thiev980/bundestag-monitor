import json
import os
import re
import pandas as pd
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

# 🔹 Stopword-Datei einlesen
stopword_file = "data/german_stopwords_full.txt"

def load_stopwords(file_path):
    stopwords = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word and not word.startswith(";"):  # Kommentare ignorieren
                stopwords.add(word)
    return stopwords

stopwords = load_stopwords(stopword_file)
print(f"✅ {len(stopwords)} Stopwords geladen.")

# 🔹 JSON-Daten einlesen
json_dir = "data/json"
documents = []
session_numbers = []

for json_file in sorted(os.listdir(json_dir)):
    if json_file.endswith(".json"):
        with open(os.path.join(json_dir, json_file), "r", encoding="utf-8") as f:
            data = json.load(f)
            text = data["text"].lower()
            text = re.sub(r"[^a-zäöüß ]", "", text)  # Sonderzeichen entfernen
            words = [word for word in text.split() if word not in stopwords]  # Stopwords filtern
            documents.append(" ".join(words))
            session_numbers.append(data["sitzungsnummer"])

# 🔹 BERTopic-Modell trainieren
print("🚀 Training von BERTopic...")
topic_model = BERTopic(language="german", calculate_probabilities=True, verbose=True)
topics, probs = topic_model.fit_transform(documents)

# 🔹 Ergebnisse als DataFrame speichern
df_topics = pd.DataFrame({
    "Sitzungsnummer": session_numbers,
    "Thema": topics
})

# 🔹 Thema-Beschreibungen holen
topic_info = topic_model.get_topic_info()
df_topic_words = pd.DataFrame(topic_info)

# 🔹 Ergebnisse speichern und anzeigen
df_topics.to_csv("data/topic_clusters.csv", encoding="utf-8", index=False)
df_topic_words.to_csv("data/topic_words.csv", encoding="utf-8", index=False)

print("✅ Themen-Clustering gespeichert: data/topic_clusters.csv & data/topic_words.csv")

# 🔹 Interaktive Visualisierung starten
topic_model.visualize_barchart(top_n_topics=10)