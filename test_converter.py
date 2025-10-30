#!/usr/bin/env python3
"""Test the CardConverter with real Anki data."""

import sys
sys.path.insert(0, '/Users/michaelkrech/_work/anki-course-tutor-mcp-server/src')

from anki_course_tutor.anki_client import CardConverter

# Simulate the real Anki note we just found
test_note = {
    "noteId": 1761771178845,
    "modelName": "AllInOne (kprim, mc, sc)",
    "fields": {
        "Question": {"value": "Welche Aussagen über Conditional Parameterization sind korrekt?"},
        "Title": {"value": "Programmierung Grundlagen"},
        "QType (0=kprim,1=mc,2=sc)": {"value": "1"},
        "Q_1": {"value": "Python"},
        "Q_2": {"value": "Java"},
        "Q_3": {"value": "HTML"},
        "Q_4": {"value": "C++"},
        "Q_5": {"value": "CSS"},
        "Answers": {"value": "1 1 0 1 0"},
        "Sources": {"value": ""},
        "Extra 1": {"value": ""},
    },
    "tags": ["BN1", "mc", "PGM", "seite5"],
    "deckName": "PGM::02_Bn1",
}

print("Testing CardConverter with AllInOne note...")
print(f"Model Name: {test_note['modelName']}\n")

card = CardConverter.from_anki_note(test_note)

if card:
    print(f"✅ Conversion successful!")
    print(f"   Card Type: {card.type}")
    print(f"   Question: {card.question[:60]}")
    print(f"   Answer: {card.answer}")
    print(f"   AllInOne Type: {card.all_in_one_type}")
    print(f"   Fields: {list(card.fields.keys()) if card.fields else 'None'}")
    print(f"   Options would be: {[v for k, v in (card.fields or {}).items() if (k.startswith('Q_') or k.startswith('Q') or k.startswith('Option')) and any(c.isdigit() for c in k)]}")
else:
    print("❌ Conversion failed!")
