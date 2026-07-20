#!/usr/bin/env python3
import sqlite3
import time
from pathlib import Path

DB_FILE = Path(__file__).parent / 'daily_hanzi.db'


def verify():
    if not DB_FILE.exists():
        zip_path = DB_FILE.with_suffix('.db.zip')
        if zip_path.exists():
            print(f"Database file '{DB_FILE.name}' not found. Extracting from '{zip_path.name}'...")
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(DB_FILE.parent)
            print("Extraction complete.")
        else:
            print(f"Error: Database file not found at {DB_FILE} or {zip_path}")
            return False

    print("Connecting to database...")
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    # 1. Check record count
    cursor.execute("SELECT COUNT(*) FROM dictionary;")
    count = cursor.fetchone()[0]
    print(f"Total records in 'dictionary' table: {count}")
    if count != 271660:
        print(f"Warning: Expected 271660 records, but found {count}.")
    else:
        print("Record count matches expected value exactly!")

    # 2. Verify lookups for common terms
    test_terms = ["木", "学习", "你好", "3D打印"]
    print("\nVerifying lookup for test terms:")
    for term in test_terms:
        start = time.perf_counter()
        cursor.execute("""
            SELECT simplified, pinyin_display, brief, meaning 
            FROM dictionary 
            WHERE simplified = ? LIMIT 1;
        """, (term,))
        result = cursor.fetchone()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        if result:
            simplified, pinyin_display, brief, meaning = result
            print(f"  Query: '{term}' -> Found in {elapsed:.3f} ms")
            print(f"    Pinyin: {pinyin_display}")
            print(f"    Brief: {brief}")
            print(f"    Detailed Meaning: {meaning[:100]}...")
        else:
            print(f"  Query: '{term}' -> NOT FOUND (Took {elapsed:.3f} ms)")

    # 3. Test query performance of index (1000 queries)
    print("\nRunning 1000 random lookup queries to test speed...")
    # Fetch 1000 random words from DB first
    cursor.execute("SELECT simplified FROM dictionary ORDER BY RANDOM() LIMIT 1000;")
    random_words = [row[0] for row in cursor.fetchall()]

    start_perf = time.perf_counter()
    for word in random_words:
        cursor.execute("SELECT brief FROM dictionary WHERE simplified = ? LIMIT 1;", (word,))
        _ = cursor.fetchone()
    end_perf = time.perf_counter()

    total_time_ms = (end_perf - start_perf) * 1000
    avg_time_ms = total_time_ms / 1000
    print(f"Completed 1000 indexed lookups in {total_time_ms:.2f} ms.")
    print(f"Average query time: {avg_time_ms:.3f} ms per query.")

    conn.close()
    return True


if __name__ == '__main__':
    verify()
