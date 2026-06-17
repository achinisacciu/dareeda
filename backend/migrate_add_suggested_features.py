"""
Migrazione manuale: aggiunge la colonna suggested_features alla tabella datasets.
Eseguire UNA SOLA VOLTA con: python migrate_add_suggested_features.py
"""

import sqlite3
from pathlib import Path

# Percorso del database SQLite
DB_PATH = Path(__file__).parent / "projects" / "dareeda.db"


def migrate():
    if not DB_PATH.exists():
        print(f"❌ Database non trovato: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Controlla se la colonna esiste già
    cursor.execute("PRAGMA table_info(datasets)")
    columns = [row[1] for row in cursor.fetchall()]

    if "suggested_features" in columns:
        print("✅ Colonna 'suggested_features' già presente — nessuna modifica necessaria.")
        conn.close()
        return

    # Aggiunge la colonna
    cursor.execute("ALTER TABLE datasets ADD COLUMN suggested_features TEXT")
    conn.commit()
    conn.close()
    print("✅ Colonna 'suggested_features' aggiunta con successo alla tabella 'datasets'.")


if __name__ == "__main__":
    migrate()
