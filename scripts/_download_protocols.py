import logging
import requests
from pathlib import Path
from datetime import datetime
import json
from typing import Optional, List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProtocolDownloader:
    BASE_URL = "https://dserver.bundestag.de/btp/20/"
    WAHLPERIODE = "20"
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.pdf_dir = base_dir / "data" / "pdfs"
        self.metadata_file = base_dir / "data" / "metadata.json"
        
        # Erstelle benötigte Verzeichnisse
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Lade existierende Metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Lädt existierende Metadata oder erstellt neue"""
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        return {
            "last_check": None,
            "protocols": {}
        }
    
    def _save_metadata(self):
        """Speichert Metadata"""
        self.metadata_file.write_text(json.dumps(self.metadata, indent=2))

    def check_protocol_exists(self, number: int) -> bool:
        """Prüft ob ein Protokoll existiert"""
        url = f"{self.BASE_URL}{self.WAHLPERIODE}{number:03d}.pdf"
        response = requests.head(url)
        return response.status_code == 200

    def find_latest_protocol(self) -> int:
        """Findet die Nummer des neuesten verfügbaren Protokolls"""
        current = 211  # Aktuell bekannte neueste Nummer
        
        while self.check_protocol_exists(current + 1):
            current += 1
            
        while not self.check_protocol_exists(current):
            current -= 1
            
        return current

    def download_protocol(self, number: int) -> Optional[Path]:
        """Lädt ein spezifisches Protokoll herunter"""
        protocol_id = f"{self.WAHLPERIODE}{number:03d}"
        pdf_path = self.pdf_dir / f"{protocol_id}.pdf"
        
        # Überspringe wenn bereits heruntergeladen
        if pdf_path.exists():
            logging.info(f"Protokoll {protocol_id} bereits vorhanden")
            return pdf_path
            
        url = f"{self.BASE_URL}{protocol_id}.pdf"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            pdf_path.write_bytes(response.content)
            
            # Aktualisiere Metadata
            self.metadata["protocols"][protocol_id] = {
                "number": number,
                "downloaded_at": datetime.now().isoformat(),
                "file_path": str(pdf_path.relative_to(self.base_dir)),
                "processed": False
            }
            self._save_metadata()
            
            logging.info(f"Protokoll {protocol_id} erfolgreich heruntergeladen")
            return pdf_path
            
        except Exception as e:
            logging.error(f"Fehler beim Download von Protokoll {protocol_id}: {e}")
            return None

    def download_latest_protocols(self, limit: int = 10) -> List[Path]:
        """Lädt die neuesten N Protokolle herunter"""
        latest = self.find_latest_protocol()
        start = max(1, latest - limit + 1)
        
        downloaded = []
        for number in range(start, latest + 1):
            if path := self.download_protocol(number):
                downloaded.append(path)
                
        return downloaded

def main():
    # Basis-Verzeichnis ist das Root-Verzeichnis des Projekts
    base_dir = Path(__file__).resolve().parent.parent
    
    downloader = ProtocolDownloader(base_dir)
    
    # Finde und lade die 10 neuesten Protokolle
    latest = downloader.find_latest_protocol()
    logging.info(f"Neuestes Protokoll: {latest}")
    
    downloaded = downloader.download_latest_protocols(10)
    logging.info(f"{len(downloaded)} Protokolle heruntergeladen")

if __name__ == "__main__":
    main()