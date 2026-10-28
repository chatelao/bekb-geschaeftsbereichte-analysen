# Roadmap: Schrittweise Konvertierung der BEKB PDF-Berichte in Markdown

Diese Roadmap beschreibt den strukturierten Plan zur schrittweisen Konvertierung aller PDF-Dokumente im Ordner `pdf/` in strukturierte Markdown-Dateien im Ordner `.md/`, inklusive der Extraktion von Bildelementen und Tabellen.

---

## 1. Übersicht & Zielsetzung

- **Ziel:** Konvertierung aller 33 PDF-Dateien (Geschäftsberichte 2003–2024 und Semesterberichte 2013–2023) in sauberes, lesbares Markdown mit referenzierten Bildern.
- **Zielordner:** `.md/` für Markdown-Dateien und `.md/images/` für extrahierte Grafiken/Bilder.
- **Werkzeuge:** Python, `pymupdf4llm` (PyMuPDF) für qualitativ hochwertige Layout- und Tabellenerfassung.

---

## 2. Bestandsaufnahme

### PDF-Dateien in `pdf/`
- **Geschäftsberichte (22 Dateien):**
  - `bekb-geschaeftsbericht-2003.pdf` bis `bekb-geschaeftsbericht-2024.pdf`
- **Semesterberichte (11 Dateien):**
  - `bekb-semesterbericht-2013.pdf` bis `bekb-semesterbericht-2023.pdf`

### Aktueller Fortschritt
- [x] Semesterberichte 2013–2015 konvertiert (`.md/bekb-semesterbericht-2013.md` bis `2015.md`)
- [ ] Semesterberichte 2016–2023 ausstehend
- [ ] Geschäftsberichte 2003–2024 ausstehend

---

## 3. Phaseneinteilung

### Phase 1: Vorbereitung & Skripterstellung
- [x] Download-Skript für fehlende Berichte erstellen (`download_reports.py`)
- [x] Erstellung eines Konvertierungsskripts (`convert_pdf_to_md.py`):
  - Automatisches Einlesen aller PDF-Dateien aus `pdf/`
  - Konvertierung mittels `pymupdf4llm.to_markdown()`
  - Bildextraktion nach `.md/images/<pdf-name>/`
  - Speichern der `.md`-Dateien in `.md/`
- [x] Abhängigkeiten verifizieren (`pymupdf4llm`, `PyMuPDF`)

### Phase 2: Konvertierung der Semesterberichte (2016–2023)
- [x] Semesterberichte 2013–2015
- [x] Batch 1: Semesterberichte 2016–2019
- [ ] Batch 2: Semesterberichte 2020–2023
- [ ] Sichtprüfung und Qualitätskontrolle der erzeugten `.md`-Dateien

### Phase 3: Konvertierung der Geschäftsberichte (2003–2024)
- [ ] Batch 1: Geschäftsberichte 2003–2009 (Ältere Berichte, einfache/klassische Layouts)
- [ ] Batch 2: Geschäftsberichte 2010–2016 (Mittlere Dekade, komplexere Tabellen)
- [ ] Batch 3: Geschäftsberichte 2017–2024 (Neueste Berichte, umfangreiche Finanztabellen)
- [ ] Überprüfung der Bild- und Tabellenintegrität

### Phase 4: Qualitätskontrolle & Nachbearbeitung
- [ ] Automatische Validierung:
  - Vollständigkeit prüfen (1:1 Abgleich PDF zu MD)
  - Prüfung abgebrochener/fehlender Bildreferenzen
- [ ] Stichprobenartige manuelle Nachbearbeitung von Tabellenformatierungen
- [ ] Dokumentation & Bereinigung von temporären Dateien

---

## 4. Richtlinien & Konventionen

- **Dateibenennung:**
  - PDF: `bekb-geschaeftsbericht-YYYY.pdf` / `bekb-semesterbericht-YYYY.pdf`
  - MD: `.md/bekb-geschaeftsbericht-YYYY.md` / `.md/bekb-semesterbericht-YYYY.md`
  - Bilder: `.md/images/<pdf-filename>/...`
- **Formatierung:**
  - Standard-Markdown-Header (`#`, `##`, `###`) für Überschriften.
  - Tabellen im Markdown-Format.
  - Bildlinks in relativer Pfadangabe (`![Alt-Text](images/...)`).

---

## 5. Meilensteine & Nachverfolgung

| Meilenstein | Beschreibung | Status |
| :--- | :--- | :--- |
| **M1** | Infrastruktur & Konvertierungsskript eingerichtet | Abgeschlossen |
| **M2** | Alle Semesterberichte (2013–2023) konvertiert | Teilweise (7/11) |
| **M3** | Geschäftsberichte 2003–2012 konvertiert | Offen |
| **M4** | Geschäftsberichte 2013–2024 konvertiert | Offen |
| **M5** | Finaler Review & Abschlussdokumentation | Offen |
