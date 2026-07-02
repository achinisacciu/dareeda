import re

import polars as pl

# Soglie
# ponytail: solo stringhe, il check normalizza sempre a str
BOOL_VALUES = {"0", "1", "true", "false", "yes", "no", "si", "t", "f", "y", "n"}
ID_KEYWORDS = re.compile(r"\b(id|key|uuid|guid|code|cod|codice|pk|fk|ref|hash)\b", re.IGNORECASE)
GEO_LAT_KW = re.compile(r"\b(lat|latitude|latitudine)\b", re.IGNORECASE)
GEO_LON_KW = re.compile(r"\b(lon|lng|longitude|longitudine)\b", re.IGNORECASE)
TEXT_MIN_AVG_LEN = 30  # media caratteri sopra cui = testo libero
CARD_ID_RATIO = 0.95  # unique/total sopra cui = quasi-ID
CARD_TEXT_RATIO = 0.50  # unique/total sopra cui = testo (se lunga)
DISCRETE_MAX_UNQ = 30  # max unique per numerico discreto

SEMANTIC_TYPES = {
    "numeric_continuous": "Numerico continuo",
    "numeric_discrete": "Numerico discreto",
    "categorical_nominal": "Categorico nominale",
    "categorical_ordinal": "Categorico ordinale",
    "boolean": "Booleano",
    "datetime": "Datetime",
    "text": "Testo libero",
    "id": "ID / quasi-ID",
    "geographic": "Geografico",
    "unknown": "Sconosciuto",
}


def detect_semantic_type(series: pl.Series) -> str:
    name = series.name
    dtype = series.dtype
    n = len(series)
    # ponytail: null_count non usato, rimosso
    valid = series.drop_nulls()
    n_unq = valid.n_unique() if len(valid) > 0 else 0
    card_r = n_unq / n if n > 0 else 0

    # 1. Datetime
    if dtype in (pl.Date, pl.Datetime, pl.Time, pl.Duration):
        return "datetime"

    # 2. Booleano (dtype o valori)
    if dtype == pl.Boolean:
        return "boolean"
    if n_unq <= 2 and set(str(v).lower() for v in valid.unique().to_list()) <= BOOL_VALUES:
        return "boolean"

    # 3. Geografico (nome colonna) — prima del check float per catturare latitude/longitude flaot
    if GEO_LAT_KW.search(name):
        return "geographic"
    if GEO_LON_KW.search(name):
        return "geographic"

    # 4. ID / quasi-ID
    if ID_KEYWORDS.search(name) and card_r >= 0.90:
        return "id"
    if card_r >= CARD_ID_RATIO and n_unq > 100:
        return "id"

    # 5. Numerico — float dopo geografico/ID per non oscurarli
    if dtype in (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
        pl.Float32,
        pl.Float64,
    ):
        if dtype in (pl.Float32, pl.Float64):
            return "numeric_continuous"
        if n_unq <= DISCRETE_MAX_UNQ:
            return "numeric_discrete"
        return "numeric_continuous"

    # 6. Stringa
    if dtype == pl.String or dtype == pl.Utf8:
        # Tenta parse datetime
        try:
            parsed = valid.cast(pl.Datetime, strict=False)
            if parsed.null_count() < len(valid) * 0.5:
                return "datetime"
        except Exception:
            pass

        # Testo libero (alta cardinalità + stringhe lunghe)
        avg_len = valid.str.len_chars().mean() if len(valid) > 0 else 0
        if avg_len is not None and avg_len >= TEXT_MIN_AVG_LEN and card_r >= CARD_TEXT_RATIO:
            return "text"

        # Categorico
        return "categorical_nominal"

    return "unknown"


def type_dataframe(df: pl.DataFrame) -> dict[str, str]:
    """Ritorna {colonna: tipo_semantico} per tutte le colonne del df."""
    return {col: detect_semantic_type(df[col]) for col in df.columns}


def group_by_semantic(typing: dict[str, str]) -> dict[str, list[str]]:
    """Raggruppa le colonne per tipo semantico."""
    groups: dict[str, list[str]] = {k: [] for k in SEMANTIC_TYPES}
    for col, stype in typing.items():
        if stype in groups:
            groups[stype].append(col)
        else:
            groups["unknown"].append(col)
    return groups

def analyze_datetime_features(df: pl.DataFrame, dt_cols: list[str]) -> dict[str, dict]:
    """Analizza le colonne datetime per frequenza e gap temporali."""
    results = {}
    for col in dt_cols:
        try:
            s = df[col].drop_nulls().cast(pl.Datetime)
            if len(s) < 2:
                continue
            
            s = s.sort()
            diffs = s.diff().drop_nulls()
            if len(diffs) == 0:
                continue
                
            median_diff = diffs.median()
            if median_diff is None:
                continue
                
            # Calcola quanti gap sono > 1.5 * median_diff
            # median_diff è un pl.Duration
            # Possiamo confrontare le duration in millisecondi
            diffs_ms = diffs.dt.total_milliseconds()
            med_ms = median_diff.total_seconds() * 1000
            
            if med_ms == 0:
                continue
                
            gaps = diffs_ms.filter(diffs_ms > med_ms * 1.5)
            n_gaps = len(gaps)
            
            # Formatta frequenza in modo leggibile (euristica base)
            freq_str = f"{med_ms}ms"
            if med_ms >= 86400000:
                freq_str = f"{int(med_ms/86400000)}D"
            elif med_ms >= 3600000:
                freq_str = f"{int(med_ms/3600000)}H"
            elif med_ms >= 60000:
                freq_str = f"{int(med_ms/60000)}min"
                
            results[col] = {
                "inferred_frequency": freq_str,
                "n_gaps": n_gaps,
                "has_gaps": n_gaps > 0
            }
        except Exception:
            pass
            
    return results
