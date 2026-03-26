import polars as pl
import re

# Soglie
BOOL_VALUES      = {0, 1, "0", "1", "true", "false", "yes", "no", "si", "no", "t", "f", "y", "n"}
ID_KEYWORDS      = re.compile(r"\b(id|key|uuid|guid|code|cod|codice|pk|fk|ref|hash)\b", re.IGNORECASE)
GEO_LAT_KW       = re.compile(r"\b(lat|latitude|latitudine)\b", re.IGNORECASE)
GEO_LON_KW       = re.compile(r"\b(lon|lng|longitude|longitudine)\b", re.IGNORECASE)
TEXT_MIN_AVG_LEN = 30    # media caratteri sopra cui = testo libero
CARD_ID_RATIO    = 0.95  # unique/total sopra cui = quasi-ID
CARD_TEXT_RATIO  = 0.50  # unique/total sopra cui = testo (se lunga)
DISCRETE_MAX_UNQ = 30    # max unique per numerico discreto

SEMANTIC_TYPES = {
    "numeric_continuous": "Numerico continuo",
    "numeric_discrete":   "Numerico discreto",
    "categorical_nominal":"Categorico nominale",
    "categorical_ordinal":"Categorico ordinale",
    "boolean":            "Booleano",
    "datetime":           "Datetime",
    "text":               "Testo libero",
    "id":                 "ID / quasi-ID",
    "geographic":         "Geografico",
    "unknown":            "Sconosciuto",
}

def detect_semantic_type(series: pl.Series) -> str:
    name   = series.name
    dtype  = series.dtype
    n      = len(series)
    n_null = series.null_count()
    valid  = series.drop_nulls()
    n_unq  = valid.n_unique() if len(valid) > 0 else 0
    card_r = n_unq / n if n > 0 else 0

    # 1. Datetime
    if dtype in (pl.Date, pl.Datetime, pl.Time, pl.Duration):
        return "datetime"

    # 2. Booleano (dtype o valori)
    if dtype == pl.Boolean:
        return "boolean"
    if n_unq <= 2 and set(str(v).lower() for v in valid.unique().to_list()) <= BOOL_VALUES:
        return "boolean"

    # 2b. Float -> sempre numerico continuo (mai ID)
    if dtype in (pl.Float32, pl.Float64):
        return "numeric_continuous"

    # 3. Geografico (nome colonna)
    if GEO_LAT_KW.search(name):
        return "geographic"
    if GEO_LON_KW.search(name):
        return "geographic"

    # 4. ID / quasi-ID
    if ID_KEYWORDS.search(name) and card_r >= 0.90:
        return "id"
    if card_r >= CARD_ID_RATIO and n_unq > 100:
        return "id"

    # 5. Numerico
    if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                 pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
                 pl.Float32, pl.Float64):
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

