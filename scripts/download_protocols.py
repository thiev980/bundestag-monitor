import os
import requests

# Zielordner für PDFs
output_dir = "plenarprotokolle"
os.makedirs(output_dir, exist_ok=True)

# Sitzungsnummern für die ersten 10 Protokolle
start_session = 210
num_protokolle = 10  # Anzahl der zu ladenden PDFs

# Base-URL
base_url = "https://dserver.bundestag.de/btp/20/20"

for i in range(num_protokolle):
    session_number = start_session + i
    pdf_url = f"{base_url}{session_number}.pdf"
    pdf_path = os.path.join(output_dir, f"plenarprotokoll_{session_number}.pdf")

    try:
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200:
            with open(pdf_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"✅ Erfolgreich heruntergeladen: {pdf_url}")
        else:
            print(f"❌ Fehler: {pdf_url} nicht gefunden")
    except Exception as e:
        print(f"⚠️ Fehler beim Laden {pdf_url}: {e}")