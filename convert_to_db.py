#!/usr/bin/env python3
import csv
import sqlite3
import sys
import time
from pathlib import Path

# Increase CSV field limit to handle potentially large fields
csv.field_size_limit(10 * 1024 * 1024)  # 10MB limit

CSV_FILE = Path(__file__).parent / 'clean_dict.csv'
DB_FILE = Path(__file__).parent / 'daily_hanzi.db'

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS dictionary (
    word_id INTEGER PRIMARY KEY,
    simplified TEXT NOT NULL,
    pinyin TEXT NOT NULL,
    pinyin_display TEXT NOT NULL,
    brief TEXT,
    origin TEXT,
    meaning TEXT,
    usage TEXT,
    tags TEXT,
    hsk_level TEXT,
    status TEXT,
    part_of_speech TEXT,
    measure_word TEXT,
    grammar_pattern TEXT,
    frequency_rank INTEGER,
    simple_example TEXT,
    valency TEXT,
    synonyms TEXT,
    antonyms TEXT,
    near_synonyms TEXT,
    near_synonym_distinction TEXT,
    collocations TEXT,
    register TEXT,
    cedict_definitions TEXT,
    src_xiandai_da INTEGER,
    src_zhonghua INTEGER,
    src_guifan INTEGER,
    src_xiandai7_py INTEGER,
    src_xiandai7 INTEGER,
    src_jindai INTEGER,
    src_gudai INTEGER,
    src_taiwan INTEGER,
    src_liangan INTEGER
);
"""

INSERT_SQL = """
INSERT OR REPLACE INTO dictionary (
    word_id, simplified, pinyin, pinyin_display, brief, origin, meaning, usage, tags,
    hsk_level, status, part_of_speech, measure_word, grammar_pattern, frequency_rank,
    simple_example, valency, synonyms, antonyms, near_synonyms, near_synonym_distinction,
    collocations, register, cedict_definitions, src_xiandai_da, src_zhonghua, src_guifan,
    src_xiandai7_py, src_xiandai7, src_jindai, src_gudai, src_taiwan, src_liangan
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?
);
"""


def convert():
    if not CSV_FILE.exists():
        zip_path = CSV_FILE.with_suffix('.csv.zip')
        if zip_path.exists():
            print(f"CSV file '{CSV_FILE.name}' not found. Extracting from '{zip_path.name}'...")
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(CSV_FILE.parent)
            print("Extraction complete.")
        else:
            print(f"Error: CSV file not found at {CSV_FILE} or {zip_path}")
            sys.exit(1)

    print("Starting conversion...")
    start_time = time.time()

    # If database file exists, delete it first to start clean
    if DB_FILE.exists():
        print(f"Deleting existing database file: {DB_FILE.name}")
        DB_FILE.unlink()

    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    # Enable write-ahead logging and synchronous off for fast insert
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = OFF;")

    print("Creating table schema...")
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()

    print("Parsing CSV and importing records in batches...")
    batch_size = 5000
    batch = []
    total_records = 0

    with open(CSV_FILE, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row

        for row in reader:
            if not row:
                continue

            # Map fields properly. Pad row if CSV columns count varies
            if len(row) < 33:
                row = row + [None] * (33 - len(row))
            elif len(row) > 33:
                row = row[:33]

            # Parse numeric fields
            # word_id is row[0]
            word_id = int(row[0]) if row[0] else None
            # frequency_rank is row[14]
            freq_rank = int(row[14]) if row[14] and row[14].isdigit() else None
            
            # Source indicator fields are columns 24 to 32 (0-indexed)
            src_fields = []
            for col_idx in range(24, 33):
                val = row[col_idx]
                if val is not None and val.strip().isdigit():
                    src_fields.append(int(val))
                else:
                    src_fields.append(0)

            # Construct finalized data row
            processed_row = [
                word_id,
                row[1], # simplified
                row[2], # pinyin
                row[3], # pinyin_display
                row[4], # brief
                row[5], # origin
                row[6], # meaning
                row[7], # usage
                row[8], # tags
                row[9], # hsk_level
                row[10], # status
                row[11], # part_of_speech
                row[12], # measure_word
                row[13], # grammar_pattern
                freq_rank,
                row[15], # simple_example
                row[16], # valency
                row[17], # synonyms
                row[18], # antonyms
                row[19], # near_synonyms
                row[20], # near_synonym_distinction
                row[21], # collocations
                row[22], # register
                row[23]  # cedict_definitions
            ] + src_fields

            batch.append(processed_row)

            if len(batch) >= batch_size:
                cursor.executemany(INSERT_SQL, batch)
                conn.commit()
                total_records += len(batch)
                print(f"  Processed {total_records} records...")
                batch = []

        # Insert remaining records
        if batch:
            cursor.executemany(INSERT_SQL, batch)
            conn.commit()
            total_records += len(batch)
            print(f"  Processed {total_records} records...")

    print("Creating indexes to optimize search queries...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_simplified ON dictionary(simplified);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_pinyin ON dictionary(pinyin);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_pinyin_display ON dictionary(pinyin_display);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dict_hsk ON dictionary(hsk_level);")
    conn.commit()

    print("Running optimize analysis...")
    cursor.execute("PRAGMA optimize;")
    conn.commit()
    conn.close()

    elapsed = time.time() - start_time
    print(f"Success! Imported {total_records} records in {elapsed:.2f} seconds.")
    print(f"SQLite database generated: {DB_FILE.name}")


if __name__ == '__main__':
    convert()
