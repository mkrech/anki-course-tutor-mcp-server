#!/usr/bin/env python3
"""Debug script to check card note type in Anki."""

import requests
import json

def main():
    # Get notes in deck
    payload = {
        "action": "findNotes",
        "version": 6,
        "params": {
            "query": 'deck:"PGM::02_Bn1"'
        }
    }
    
    resp = requests.post("http://localhost:8765", json=payload)
    result = resp.json()
    print("Notes in deck:", result)
    
    if result.get("result"):
        # Get info about all notes
        note_ids = result["result"]
        payload = {
            "action": "notesInfo",
            "version": 6,
            "params": {
                "notes": note_ids
            }
        }
        
        resp = requests.post("http://localhost:8765", json=payload)
        info = resp.json()
        for note in info['result']:
            print(f"\n📋 Note ID: {note['noteId']}")
            print(f"   Model: {note.get('modelName')}")
            print(f"   Tags: {note.get('tags')}")
            fields = note.get('fields', {})
            print(f"   Fields: {list(fields.keys())}")
            # Show first field
            if fields:
                first_key = list(fields.keys())[0]
                val = fields[first_key].get('value', '')[:80] if isinstance(fields[first_key], dict) else str(fields[first_key])[:80]
                print(f"   First field ({first_key}): {val}")

if __name__ == "__main__":
    main()
