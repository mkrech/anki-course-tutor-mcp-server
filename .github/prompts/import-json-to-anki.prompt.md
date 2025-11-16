---
description: Import flashcards from JSON files into Anki decks with page filtering
---

$ARGUMENTS
<!-- IMPORT-JSON-TO-ANKI:START -->
**Language**: Always communicate in German (Deutsch) with the user.

**Guardrails**
- Ensure Anki Desktop is running with AnkiConnect addon installed before starting
- Validate JSON file structure (must contain `sections` array)
- Create deck if it doesn't exist
- **Maximum 5 pages per import** - Prevents overwhelming generation and ensures quality
- Support batch imports (recommended: 10-20 cards per batch)
- Handle errors gracefully with clear error messages
- Show progress during import (e.g., "Importing cards 1-20 of 150...")
- If user requests more than 5 pages, suggest breaking into multiple imports

**Required JSON Structure**

The JSON file must contain a `sections` array from parsed PDF slides:

```json
{
  "file_path": "path/to/source.pdf",
  "metadata": {
    "parser": "docling",
    "filename": "02_tud_PGM02_BN1.pdf",
    "source_type": "slides",
    "document_kind": "slides",
    "lecture_nr": 2,
    "topic": "BN1"
  },
  "sections": [
    {
      "id": "section_id",
      "title": "Section Title",
      "content": "Section content with key concepts, definitions, formulas...",
      "level": 1,
      "page": 5,
      "parent_id": null,
      "image_path": "data/intermediate/slide_images/filename/slide_5.png"
    }
  ],
  "stats": {
    "total_sections": 78,
    "total_chars": 11964
  }
}
```

**The AI will automatically generate flashcards from these sections.**

**Steps**

1. **Load Sections JSON** - Parse the sections from the JSON file
2. **Analyze Sections** - Use AI to analyze content and determine optimal flashcards
3. **Generate Flashcards** - AI creates question-answer pairs with appropriate card types
4. **Check Anki Connection** - Verify Anki Desktop is running with AnkiConnect
5. **List Available Decks** - Show existing Anki decks or option to create new deck
6. **Select or Create Deck** - Choose existing deck or specify new deck name (e.g., "PGM::02_Bn1")
7. **Optional: Set Page Range** - Specify which pages to process (e.g., "pages 1-10" or "page 5" or leave empty for all)
8. **Optional: Set Card Type Distribution** - Specify preferred card type mix (see Card Type Distribution section below)
9. **Review Generated Cards** - Show sample of generated cards for approval
10. **Confirm Import** - Review the import plan (number of cards, deck name, page range, card types)
11. **Execute Import** - Use batch import to create cards in Anki
12. **Verify Import** - Check that cards were created successfully in Anki

**Page Filtering**
- **Default: First 5 pages only** - Always limit to max 5 pages unless user specifies fewer
- **Single page**: "page 5" or "p5"
- **Page range (max 5)**: "pages 1-5" or "p1-5" 
- **Multiple ranges (max 5 total)**: "pages 1-3, 8-9" or "p1-3,8-9" (5 pages total)
- **More than 5 pages requested**: Suggest splitting into multiple imports
  - Example: "Seiten 1-10" → "Zu viele Seiten! Bitte maximal 5 Seiten pro Import. Mach zuerst 1-5, dann 6-10."

**Card Type Distribution**

Users can specify their preferred card type mix when generating flashcards. The AI will attempt to match this distribution:

**Default Distribution (if not specified):**
- **Cloze: 55%** (Majority) - Fill-in-the-blank for definitions, formulas, key concepts
- **All-in-One (KPRIM/MC/SC): 45%** - Multiple choice, single choice, K-Prim statements
  - KPRIM: 30% - 4 statements with T/F evaluation (ideal for comparisons, properties)
  - MC: 10% - Multiple correct answers (concepts with several valid aspects)
  - SC: 5% - Single correct answer (clear-cut questions)
- **Basic: 0%** (NEVER USE) - Basic cards are NOT allowed

**User Preferences Examples:**
- **"Mehrheit Cloze, viel KPRIM"** 
  - Cloze: 55%, KPRIM: 35%, MC: 7%, SC: 3%, Basic: 0%
- **"Nur KPRIM und Cloze"**
  - KPRIM: 50%, Cloze: 50%, Basic: 0%, MC: 0%, SC: 0%
- **"Balanced Mix"**
  - Cloze: 40%, KPRIM: 30%, MC: 20%, SC: 10%, Basic: 0%

**How to Specify:**
During the workflow, when asked, the user can say:
- **"Standard Verteilung"** or **"Default"** → Uses default distribution (NO Basic!)
- **"Mehrheit Cloze und KPRIM"** → AI interprets as Cloze 50%, KPRIM 40%, MC 7%, SC 3%
- **"Nur Cloze"** → 100% Cloze cards
- **Custom percentages** → "50% Cloze, 30% KPRIM, 20% MC"

**AI Generation Strategy:**
1. Analyze section content for suitability to each card type
2. Generate cards attempting to match user's preferred distribution
3. Adapt if content doesn't fit (e.g., can't force KPRIM if no 4-way comparisons exist)
4. Show actual distribution in import plan for user review

**Note Types & Card Types**

The system supports these card types with automatic note type mapping:

| Card Type | Anki Note Type | Fields | Description |
|-----------|----------------|--------|-------------|
| `cloze` | Cloze | Text, Extra | Fill-in-the-blank cards with {{c1::deletions}} |
| `kprim` | AllInOne (kprim, mc, sc) | Question, Answer, Q_1-Q_5, Extra, Sources | K-Prim cards with 4 statements (each True/False) |
| `mc` | AllInOne (kprim, mc, sc) | Question, Answer, Q_1-Q_5, Extra, Sources | Multiple choice (multiple correct answers) |
| `sc` | AllInOne (kprim, mc, sc) | Question, Answer, Q_1-Q_5, Extra, Sources | Single choice (one correct answer) |

**⚠️ WICHTIG: Basic Cards sind NICHT erlaubt!**
- Verwende IMMER Cloze, KPRIM, MC oder SC
- Konvertiere einfache Fragen zu Cloze-Format
- Beispiel: "Was ist X?" → "X ist {{c1::...}}"

**WICHTIG: Note Type Name**
- Der korrekte Note Type Name in Anki ist: **"AllInOne (kprim, mc, sc)"** (NICHT "All-in-One")
- Beim Import MUSS dieser exakte Name verwendet werden

**AllInOne Note Type Structure:**
- **Question**: Main question text
- **Answer**: Correct answer(s) or solution explanation
- **Q_1 to Q_5**: Answer options or statements
- **Extra**: Additional context or explanations
- **Sources**: Source reference (e.g., "Folie 5", "Homework-1 Task 3")

**Note Type Requirements:**
- Ensure the note types exist in Anki before importing
- Use `mcp_anki_list_note_types` to check available note types
- The correct name is "AllInOne (kprim, mc, sc)" not "All-in-One"
- If missing, create them manually or the import will fail

**Example Workflow**

```
# 1. Start import workflow
You: Importiere JSON in Anki

AI: 🔍 Prüfe Anki-Verbindung...
    ✓ Anki läuft und AnkiConnect ist verfügbar
    
    📚 Verfügbare Decks (7):
    1. Default
    2. PGM
    3. PGM::01_Intro
    4. PGM::02_Bn1
    5. PGM::03_Bn2
    6. PGM::04_Bn3
    7. PGM::Homework1
    
    Wähle ein Deck (1-7) oder gib einen neuen Deck-Namen ein:

# 2. User selects or creates deck
You: PGM::02_Bn1

AI: ✓ Deck "PGM::02_Bn1" ausgewählt
    
    Welche JSON-Datei soll verarbeitet werden?
    Verfügbare Dateien:
    - data/input/intermediate/01_tud_PGM01_intro.json (78 sections)
    - data/input/intermediate/02_tud_PGM02_BN1.json (78 sections)
    - data/input/intermediate/03_tud_PGM03_BN2.json (65 sections)
    - data/input/intermediate/homework-1.json (4 sections)
    
    Oder gib einen eigenen Pfad ein:

# 3. User provides JSON file
You: data/input/intermediate/02_tud_PGM02_BN1.json

AI: 📂 JSON-Datei gefunden: 02_tud_PGM02_BN1.json
    📊 Enthält 78 Sections (Seiten 1-62)
    
    ⚠️  Hinweis: Maximal 5 Seiten pro Import für beste Qualität!
    
    Welche Seiten möchtest du verarbeiten? (max 5)
    - Seiten 1-5 (empfohlen für ersten Import)
    - Seite 5
    - Seiten 10-14
    
    Gib Seitenbereich ein (max 5 Seiten):

# 4. User specifies page range
You: Seiten 1-5

AI: ✓ Filter gesetzt: Seiten 1-5 (5 Seiten)
    
    Welche Kartentyp-Verteilung möchtest du? (optional)
    
    📊 Standard-Verteilung (Default):
    - Cloze: 50% (Mehrheit - Lückentexte)
    - KPRIM: 25% (4 Aussagen T/F)
    - MC: 10% (Mehrere richtige Antworten)
    - SC: 5% (Eine richtige Antwort)
    - Basic: 10% (Einfache Frage-Antwort)
    
    Beispiele:
    - "Standard" / "Default" → nutzt obige Verteilung
    - "Mehrheit Cloze, viel KPRIM, wenig Basic" → 50% Cloze, 35% KPRIM, 5% Basic, 10% andere
    - "Nur Cloze und KPRIM" → 50% Cloze, 50% KPRIM
    - "50% Cloze, 30% KPRIM, 20% Basic"
    
    Gib Verteilung ein (oder Enter für Standard):

# 4b. User specifies card distribution (optional)
You: Mehrheit Cloze, viel KPRIM, wenig Basic

AI: ✓ Kartentyp-Präferenz: Cloze (50%), KPRIM (35%), MC (10%), SC (3%), Basic (2%)
    
    🤖 Generiere Flashcards aus Sections...
    ⏳ Analysiere Sections auf Seiten 1-5...
    ✓ 24 Karten generiert
    
    📊 Nach Filter: 24 Flashcards
    
    📋 Import-Plan:
    - Quell-Datei: 02_tud_PGM02_BN1.json (sections)
    - Generiert: 24 Karten aus Seiten 1-5
    - Ziel-Deck: PGM::02_Bn1 (existiert bereits)
    - Kartentypen: 12× Cloze, 8× KPRIM, 2× MC, 1× SC, 1× Basic
    - Verteilung: Cloze 50%, KPRIM 33%, MC 8%, SC 4%, Basic 4% ✓ (nah an Präferenz)
    
    📝 Beispiel-Karten:
    1. [Cloze] "Ein BN faktoriziert als P(X1,...,Xn) = {{c1::∏ᵢ P(Xᵢ|Pa(Xᵢ))}}" (Seite 5)
    2. [KPRIM] "Welche Aussagen über Conditional Independence sind korrekt?" (Seite 4)
    3. [MC] "Welche Parameterisierungen sind effizienter als Enumeration?" (Seite 6)
    
    Soll ich mit dem Import beginnen? (ja/nein)

# 5. User confirms
You: ja

AI: 📥 Starte Import...
    
    ⏳ Importiere Karten 1-20 von 24...
    ✓ Batch 1/2 erfolgreich (20 Karten)
    ⏳ Importiere Karten 21-24 von 24...
    ✓ Batch 2/2 erfolgreich (4 Karten)
    
    🎉 Import abgeschlossen!
    
    📊 Ergebnis:
    - Erfolgreich: 24 Karten
    - Fehler: 0
    - Duplikate übersprungen: 0
    - Dauer: 6 Sekunden (inkl. AI-Generierung)
    
    Die Karten sind jetzt in Anki im Deck "PGM::02_Bn1" verfügbar! 🎊
    
    💡 Tipp: Für Seiten 6-10, starte einen neuen Import mit "Seiten 6-10"

# Example: User tries too many pages
You: Seiten 1-15

AI: ⚠️  Zu viele Seiten! Maximum ist 5 Seiten pro Import.
    
    📋 Vorschlag:
    - Import 1: Seiten 1-5
    - Import 2: Seiten 6-10
    - Import 3: Seiten 11-15
    
    Soll ich mit Seiten 1-5 starten? (ja/nein/andere)

# Alternative: Create new deck during import
You: Importiere JSON in Anki

AI: 🔍 Prüfe Anki-Verbindung...
    ✓ Anki läuft
    
    📚 Verfügbare Decks (7):
    1. Default
    2. PGM
    [...]
    
    Wähle ein Deck (1-7) oder gib einen neuen Deck-Namen ein:

You: PGM::05_Bn4

AI: ✓ Neues Deck "PGM::05_Bn4" wird erstellt
    
    Welche JSON-Datei soll verarbeitet werden?

You: data/input/intermediate/05_tud_PGM05_BN4.json

AI: 📂 JSON-Datei gefunden
    📊 Enthält 65 Sections
    
    🤖 Generiere Flashcards...
    ✓ 124 Karten generiert
    
    Welche Seiten möchtest du importieren?

You: alle

AI: ✓ Alle 124 Karten werden importiert
    
    📋 Import-Plan:
    - Quell-Datei: 05_tud_PGM05_BN4.json (sections)
    - Seiten: Alle (124 Karten)
    - Ziel-Deck: PGM::05_Bn4 (wird neu erstellt)
    - Kartentypen: 85× Basic, 28× KPRIM, 8× Cloze, 3× MC
    
    Soll ich mit dem Import beginnen? (ja/nein)

You: ja

AI: 📥 Starte Import...
    ✓ Deck "PGM::05_Bn4" erstellt
    ⏳ Importiere Karten 1-20 von 124...
    ✓ Batch 1/7 erfolgreich (20 Karten)
    ⏳ Importiere Karten 21-40 von 124...
    ✓ Batch 2/7 erfolgreich (20 Karten)
    [...]
    ⏳ Importiere Karten 121-124 von 124...
    ✓ Batch 7/7 erfolgreich (4 Karten)
    
    🎉 Import abgeschlossen! 124 Karten erfolgreich importiert.

# Short form: All-in-one command
You: Generiere Karten aus data/input/intermediate/homework-1.json und importiere in neues Deck PGM::Homework1, nur Seite 1

AI: 🔍 Prüfe Anki-Verbindung...
    ✓ Anki läuft
    📂 JSON-Datei gefunden: homework-1.json (4 sections)
    
    🤖 Generiere Flashcards aus Sections...
    ✓ 12 Karten generiert
    ✓ Filter gesetzt: Seite 1
    📊 Nach Filter: 3 Flashcards
    
    📋 Import-Plan:
    - Quell-Datei: homework-1.json (sections)
    - Seite: 1 (3 Karten)
    - Ziel-Deck: PGM::Homework1 (wird neu erstellt)
    
    Soll ich mit dem Import beginnen? (ja/nein)

You: ja

AI: 📥 Starte Import...
    ✓ Deck "PGM::Homework1" erstellt
    ⏳ Importiere Karten 1-3 von 3...
    ✓ Batch 1/1 erfolgreich (3 Karten)
    
    🎉 Import abgeschlossen! 3 Karten erfolgreich importiert.
```

**Troubleshooting**
- **Anki not running**: Start Anki Desktop and ensure AnkiConnect addon is installed
- **JSON file not found**: Check the file path is correct relative to workspace root
- **Invalid JSON structure**: Ensure the file has a "sections" array with required fields
- **Deck already exists**: Cards will be added to existing deck (duplicates are checked by Anki)
- **Import errors**: Check Anki's error log and ensure note types exist
- **Wrong note type name**: Use "AllInOne (kprim, mc, sc)" not "All-in-One"
- **Check available note types**: Use `mcp_anki_list_note_types` tool first

**Implementation Details**

The import workflow:

**1. Load & Parse Sections**
```python
data = read_json_file(file_path)
if "sections" not in data:
    raise ValueError("JSON must contain 'sections' array")

sections = data["sections"]
metadata = data.get("metadata", {})
```

**2. AI-Powered Flashcard Generation**

For each section, the AI analyzes:
- **Title**: Main concept or topic
- **Content**: Definitions, formulas, examples, explanations
- **Page**: Source reference
- **Level**: Section hierarchy

The AI generates flashcards following these principles:

**Card Type Selection (respects user's distribution preference):**

**Default Distribution (if user doesn't specify):**
- **Cloze: 55%** → Definitions with blanks, formulas with omissions, key concepts
- **KPRIM: 30%** → Comparisons with 4 aspects, property evaluations (each T/F)
- **MC: 10%** → Questions with multiple valid answers
- **SC: 5%** → Questions with one correct answer
- **Basic: 0%** → NEVER use Basic cards! Convert to Cloze instead

**User can request custom distributions:**
- "Mehrheit Cloze, viel KPRIM" → Cloze 55%, KPRIM 35%, MC 7%, SC 3%
- "Nur Cloze und KPRIM" → Cloze 50%, KPRIM 50%
- "Balanced" → More even distribution across all types

**Content-to-Card-Type Mapping:**
- **Definitions with key terms** → `cloze` cards (e.g., "Ein BN ist {{c1::ein gerichteter azyklischer Graph}}")
- **Formulas with variables** → `cloze` cards (e.g., "P(X1,...,Xn) = {{c1::∏ᵢ P(Xᵢ|Pa(Xᵢ))}}")
- **Comparisons with 4 aspects** → `kprim` cards (4 statements, each T/F)
- **Questions with multiple valid answers** → `mc` cards
- **Questions with one correct answer** → `sc` cards
- **Simple facts when no other type fits** → `basic` cards (minimized by default)

**Quality Guidelines:**
- **EXACTLY 1 card per section** (not 2-4, just 1!)
- Focus on the MOST IMPORTANT concept from the section
- Atomic cards (one concept per card)
- Clear, concise questions
- Complete, accurate answers
- Relevant tags and metadata
- **Respect user's card type distribution preference while adapting to content**

**AI Prompt Template:**
```
You are an expert at creating educational flashcards from lecture content.

Section Information:
- Title: {title}
- Content: {content}
- Page: {page}
- Topic: {topic from metadata}

User's Card Type Distribution Preference:
- Cloze: {cloze_pct}%
- KPRIM: {kprim_pct}%
- MC: {mc_pct}%
- SC: {sc_pct}%
- Basic: 0% (NEVER USE!)

Generate high-quality flashcards following these rules:

1. CARD TYPES (NEVER use Basic!):
   - Fill-in-blanks → cloze (use {{c1::text}} format) - PRIORITIZE for definitions and facts
   - 4-way comparisons → kprim (4 statements, mark each T/F in answer) - USE when content has 4 comparable aspects
   - Multiple correct options → mc (list all correct in answer)
   - Single correct option → sc (one correct answer)
   - **IMPORTANT**: Convert all simple facts to Cloze format instead of Basic!

2. DISTRIBUTION STRATEGY:
   - Aim to match user's preferred percentages (Cloze ~55%, KPRIM ~30%, MC ~10%, SC ~5%)
   - Adapt if content doesn't naturally fit (e.g., can't force KPRIM without 4 aspects)
   - ALWAYS convert simple Q&A to Cloze format
   - Examples:
     * "Das Bayesian Network ist ein gerichteter Graph" 
       → Basic: "Was ist ein Bayesian Network?"
       → Cloze (BETTER if user wants majority Cloze): "Ein Bayesian Network ist {{c1::ein gerichteter azyklischer Graph}}."

3. QUALITY:
   - Clear, unambiguous questions
   - Complete, accurate answers
   - Include formulas, symbols, technical terms
   - Add context in Extra field when helpful
   - Reference source in Sources field (e.g., "Folie {page}")

4. OUTPUT FORMAT (JSON):
{
  "question": "...",
  "answer": "...",
  "type": "cloze|kprim|mc|sc",  // NEVER "basic"!
  "page": {page},
  "chapter": "{topic}",
  "tags": ["tag1", "tag2"],
  "fields": {
    "Q_1": "Statement/option 1",  // for kprim/mc/sc
    "Q_2": "Statement/option 2",
    "Q_3": "Statement/option 3",
    "Q_4": "Statement/option 4",
    "Q_5": "Statement/option 5",  // optional
    "Extra": "Additional context",
    "Sources": "Folie {page}"
  }
}

**IMPORTANT: Generate EXACTLY 1 flashcard per section. Focus on the single most important concept.**
```

**3. Filter by Page Range (Optional)**
```python
if page_filter:
    cards = [c for c in cards if c["page"] in page_range]
```

**4. Batch Import to Anki**

**WICHTIG: Verwende den korrekten Note Type Namen!**
- Für KPRIM/MC/SC: `"AllInOne (kprim, mc, sc)"` (NICHT "All-in-One")
- Prüfe verfügbare Note Types mit `mcp_anki_list_note_types` vor dem Import

```python
def build_fields(card: dict) -> dict:
    card_type = card.get("type", "basic")
    
    if card_type == "basic":
        return {
            "Front": card["question"],
            "Back": card["answer"]
        }
    
    elif card_type == "cloze":
        return {
            "Text": card["question"],
            "Extra": card.get("fields", {}).get("Extra", "")
        }
    
    else:  # kprim, mc, sc - all use AllInOne (kprim, mc, sc) note type
        fields = {
            "Question": card["question"],
            "Answer": card["answer"],
        }
        
        # Add Q_1 to Q_5 if available
        card_fields = card.get("fields", {})
        for i in range(1, 6):
            key = f"Q_{i}"
            fields[key] = card_fields.get(key, "")
        
        # Add Extra and Sources
        fields["Extra"] = card_fields.get("Extra", "")
        fields["Sources"] = card_fields.get("Sources", f"Folie {card.get('page', '?')}")
        
        return fields

def build_note_type(card_type: str) -> str:
    """Map card type to Anki note type name"""
    if card_type == "basic":
        return "Basic"
    elif card_type == "cloze":
        return "Cloze"
    else:  # kprim, mc, sc
        return "AllInOne (kprim, mc, sc)"  # IMPORTANT: Use exact name!

def build_tags(card: dict) -> list:
    tags = []
    
    # Add chapter/topic tag
    if "chapter" in card:
        tags.append(f"chapter-{card['chapter']}")
    
    # Add page tag
    if "page" in card:
        tags.append(f"page-{card['page']}")
    
    # Add card type tag
    if "type" in card:
        tags.append(card["type"])
    
    # Add custom tags
    if "tags" in card:
        tags.extend(card["tags"])
    
    return tags

# Example import
notes = []
for card in cards:
    note = {
        "type": build_note_type(card["type"]),  # Use correct note type name!
        "deck": "PGM::02_Bn1",
        "fields": build_fields(card),
        "tags": build_tags(card)
    }
    notes.append(note)

# Batch import
result = mcp_anki_batch_create_notes(notes=notes, allow_duplicate=False)
```

**Reference**
- Available MCP Tools: `mcp_anki_list_decks`, `mcp_anki_create_deck`, `mcp_anki_create_note`, `mcp_anki_batch_create_notes`
- Batch size: 10-20 cards recommended (max: 50)
- Duplicate handling: Set `allow_duplicate: false` to skip existing cards
- Tags: Automatically add chapter tag and page number tag (e.g., ["chapter-02", "page-5"])
<!-- IMPORT-JSON-TO-ANKI:END -->
