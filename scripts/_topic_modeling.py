import json
import os
import re
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

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

# 🔹 Feature-Extraktion (Bag-of-Words)
vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words=list(stopwords))
X = vectorizer.fit_transform(documents)

# 🔹 LDA-Modell trainieren
num_topics = 5  # Anzahl der Themen
lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
lda.fit(X)

# 🔹 Top-Wörter pro Thema extrahieren
def get_top_words(model, feature_names, n_top_words=10):
    topics = {}
    for topic_idx, topic in enumerate(model.components_):
        topics[f"Thema {topic_idx+1}"] = [feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
    return topics

top_words = get_top_words(lda, vectorizer.get_feature_names_out())

# 🔹 Ergebnisse als DataFrame anzeigen
df_topics = pd.DataFrame(top_words)

# Alternative: DataFrame ausgeben oder speichern
print(df_topics)

# Optional: Speichern als CSV
df_topics.to_csv("data/topic_clustering.csv", encoding="utf-8", index=False)
print("✅ Themen-Clustering gespeichert: data/topic_clustering.csv")