import os
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv  # 🔹 Ladet .env Datei
import pandas as pd

# 🔹 .env Datei laden
load_dotenv()

# 🔹 OpenAI Client initialisieren
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Pfad zu JSON-Dateien
json_dir = "data/json"
output_file = "data/llm_topics.csv"

# 🔹 Ergebnisse speichern
results = []

# 🔹 Protokolle durchgehen
for json_file in sorted(os.listdir(json_dir)):
    if json_file.endswith(".json"):
        with open(os.path.join(json_dir, json_file), "r", encoding="utf-8") as f:
            data = json.load(f)
            session_number = data["sitzungsnummer"]
            text = data["text"][:2000]  # Begrenzung auf 2000 Zeichen wegen OpenAI-Token-Limit

            # 🔹 LLM-gestützte Themenextraktion
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Du bist ein NLP-Experte für Bundestagsdebatten."},
                        {"role": "user", "content": f"Extrahiere die Hauptthemen dieser Bundestagsdebatte:\n{text}"}
                    ]
                )
                topics = response.choices[0].message.content
            except Exception as e:
                topics = f"Fehler bei Sitzung {session_number}: {e}"

            # 🔹 Ergebnisse speichern
            results.append({"Sitzungsnummer": session_number, "Themen": topics})

# 🔹 Speichern als CSV
df_topics = pd.DataFrame(results)
df_topics.to_csv(output_file, encoding="utf-8", index=False)

print(f"✅ LLM-gestützte Themenextraktion gespeichert: {output_file}")