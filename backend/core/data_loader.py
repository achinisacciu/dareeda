from pathlib import Path
import polars as pl

SUPPORTED = {".csv", ".xlsx", ".xls", ".json"}

def load_file(filepath: str | Path) -> pl.DataFrame:
    path = Path(filepath)
    ext  = path.suffix.lower()

    if ext not in SUPPORTED:
        raise ValueError(f"Formato non supportato: {ext}. Usa CSV, XLSX o JSON.")

    if ext == ".csv":
        return _load_csv(path)
    elif ext in (".xlsx", ".xls"):
        return _load_excel(path)
    elif ext == ".json":
        return _load_json(path)

def _load_csv(path: Path) -> pl.DataFrame:
    try:
        return pl.read_csv(
            path,
            infer_schema_length=10_000,
            try_parse_dates=True,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception:
        # Fallback con separator auto-detect
        return pl.read_csv(path, separator=";", infer_schema_length=10_000, ignore_errors=True)

def _load_excel(path: Path) -> pl.DataFrame:
    return pl.read_excel(path, infer_schema_length=10_000)

def _load_json(path: Path) -> pl.DataFrame:
    try:
        return pl.read_json(path)
    except Exception:
        # Prova NDJSON (newline-delimited)
        return pl.read_ndjson(path)

def get_memory_mb(df: pl.DataFrame) -> float:
    return round(df.estimated_size("mb"), 3)

def get_preview(df: pl.DataFrame, n: int = 20) -> list[dict]:
    return df.head(n).to_dicts()
