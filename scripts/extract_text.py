import pdfplumber
import os
import json

# Pfade definieren
input_dir = "data/pdfs"  # PDF-Speicherort
output_dir = "data/json"  # JSON-Speicherort
os.makedirs(output_dir, exist_ok=True)

# Alle PDFs verarbeiten
for pdf_file in sorted(os.listdir(input_dir)):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(input_dir, pdf_file)
        session_number = pdf_file.split(".")[0]  # Annahme: "20210.pdf" -> "20210"
        
        # Text aus PDF extrahieren
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        
        # Strukturierte Daten speichern
        protokoll_data = {
            "sitzungsnummer": session_number,
            "text": text
        }
        
        json_path = os.path.join(output_dir, f"{session_number}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(protokoll_data, f, ensure_ascii=False, indent=4)

        print(f"✅ Verarbeitet: {pdf_file} -> {json_path}")