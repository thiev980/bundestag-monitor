# scripts/protocol_parser.py
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Speech:
    speaker: str
    party: Optional[str]
    content: str
    time: Optional[str]
    topic: Optional[str]

@dataclass
class Interjection:
    speaker: Optional[str]
    party: Optional[str]
    content: str

@dataclass
class ParsedProtocol:
    protocol_id: str
    date: datetime
    start_time: str
    president: str
    speeches: List[Speech]
    interjections: List[Interjection]
    voting_results: List[Dict]

logging.basicConfig(level=logging.INFO)

class ProtocolParser:
    def __init__(self):
        # Regex patterns für verschiedene Elemente
        self.speaker_pattern = re.compile(r"^(.+?)\s*\((.+?)\):")
        self.time_pattern = re.compile(r"\((\d{2}:\d{2})\s*Uhr\)")
        self.protocol_id_pattern = re.compile(r"Plenarprotokoll\s+(\d+/\d+)")
        self.date_pattern = re.compile(r"Berlin,\s+\w+,\s+den\s+(\d+\.\s+\w+\s+\d{4})")
        self.president_pattern = re.compile(r"Präsident(?:in)?\s+([^:]+):")
        self.topic_pattern = re.compile(r"Tagesordnungspunkt\s+(\d+\w*):")
        self.voting_pattern = re.compile(r"Namentliche\s+Abstimmung")
        self.interjection_pattern = re.compile(r"\((.*?)\)")

    def parse_pdf(self, pdf_path: Path) -> ParsedProtocol:
        """Parst ein Protokoll-PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extrahiere Metadaten von der ersten Seite
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # Basis-Informationen
                protocol_id = self._extract_protocol_id(text)
                date = self._extract_date(text)
                start_time = self._extract_start_time(text)
                president = self._extract_president(text)
                
                # Parse alle Seiten
                speeches = []
                interjections = []
                voting_results = []
                
                current_speech = None
                
                for page in pdf.pages:
                    text = page.extract_text()
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Versuche Redner zu identifizieren
                        speaker_match = self.speaker_pattern.match(line)
                        if speaker_match:
                            if current_speech:
                                speeches.append(current_speech)
                            
                            current_speech = Speech(
                                speaker=speaker_match.group(1),
                                party=speaker_match.group(2),
                                content=line[speaker_match.end():],
                                time=self._extract_time(line),
                                topic=None
                            )
                        elif current_speech:
                            # Prüfe auf Zwischenrufe
                            if '(' in line and ')' in line:
                                interjection = self._parse_interjection(line)
                                if interjection:
                                    interjections.append(interjection)
                            else:
                                current_speech.content += '\n' + line
                
                if current_speech:
                    speeches.append(current_speech)
                
                return ParsedProtocol(
                    protocol_id=protocol_id,
                    date=date,
                    start_time=start_time,
                    president=president,
                    speeches=speeches,
                    interjections=interjections,
                    voting_results=voting_results
                )
                
        except Exception as e:
            logging.error(f"Fehler beim Parsen von {pdf_path}: {e}")
            raise

    def _extract_protocol_id(self, text: str) -> str:
        """Extrahiert die Protokoll-ID (z.B. '20/123')"""
        match = self.protocol_id_pattern.search(text)
        if not match:
            raise ValueError("Keine Protokoll-ID gefunden")
        return match.group(1)

    def _extract_date(self, text: str) -> datetime:
        """Extrahiert das Datum des Protokolls"""
        match = self.date_pattern.search(text)
        if not match:
            raise ValueError("Kein Datum gefunden")
            
        date_str = match.group(1)
        # Konvertiere deutsche Monatsnamen
        month_map = {
            'Januar': '01', 'Februar': '02', 'März': '03',
            'April': '04', 'Mai': '05', 'Juni': '06',
            'Juli': '07', 'August': '08', 'September': '09',
            'Oktober': '10', 'November': '11', 'Dezember': '12'
        }
        
        for german, num in month_map.items():
            date_str = date_str.replace(german, num)
            
        try:
            return datetime.strptime(date_str, "%d. %m %Y")
        except ValueError as e:
            logging.error(f"Fehler beim Parsen des Datums: {date_str}")
            raise ValueError(f"Ungültiges Datumsformat: {e}")

    def _extract_start_time(self, text: str) -> str:
        """Extrahiert die Startzeit der Sitzung"""
        match = re.search(r"Beginn:\s*(\d{1,2}\.\d{2})\s*Uhr", text)
        if not match:
            logging.warning("Keine Startzeit gefunden, verwende '00:00'")
            return "00:00"
        return match.group(1).replace(".", ":")

    def _extract_president(self, text: str) -> str:
        """Extrahiert den/die Bundestagspräsident/in"""
        match = self.president_pattern.search(text)
        if not match:
            logging.warning("Kein/e Präsident/in gefunden")
            return "Unbekannt"
        return match.group(1).strip()

    def _extract_time(self, text: str) -> Optional[str]:
        match = self.time_pattern.search(text)
        return match.group(1) if match else None

    def _parse_interjection(self, text: str) -> Optional[Interjection]:
        match = self.interjection_pattern.search(text)
        if not match:
            return None
            
        content = match.group(1)
        # Versuche Sprecher und Partei zu extrahieren
        speaker_match = self.speaker_pattern.search(content)
        if speaker_match:
            return Interjection(
                speaker=speaker_match.group(1),
                party=speaker_match.group(2),
                content=content[speaker_match.end():].strip()
            )
        return Interjection(
            speaker=None,
            party=None,
            content=content
        )
    
    def _extract_topic_and_subtopic(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extrahiert Tagesordnungspunkt und Unterpunkt"""
        topic_match = self.topic_pattern.search(text)
        if not topic_match:
            return None, None
            
        topic = topic_match.group(1)
        # Suche nach Unterpunkt
        subtopic_match = re.search(rf"{topic}\s*(\w+)\s*:", text)
        subtopic = subtopic_match.group(1) if subtopic_match else None
        
        return topic, subtopic
    
    def _parse_speech_content(self, text: str) -> Tuple[str, List[Interjection]]:
        """Parst Redetext und extrahiert Zwischenrufe"""
        interjections = []
        speech_parts = []
        current_pos = 0
        
        for match in re.finditer(r'\((.*?)\)', text):
            # Text vor dem Zwischenruf
            speech_parts.append(text[current_pos:match.start()].strip())
            
            interjection_text = match.group(1)
            # Prüfe ob es ein Zwischenruf ist (nicht nur Zeitangabe etc.)
            if not self.time_pattern.match(interjection_text):
                interjection = self._parse_interjection(interjection_text)
                if interjection:
                    interjections.append(interjection)
                
            current_pos = match.end()
            
        # Rest des Texts
        speech_parts.append(text[current_pos:].strip())
        
        return ' '.join(speech_parts), interjections