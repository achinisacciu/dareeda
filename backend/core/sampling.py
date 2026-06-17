import polars as pl
from core.config import settings


def maybe_sample(df: pl.DataFrame) -> tuple[pl.DataFrame, bool, int | None]:
    """
    Ritorna (df_finale, sampled: bool, sample_n: int | None).
    Se n_rows > soglia, campiona a settings.sample_size righe casuali.
    """
    n = len(df)
    if n <= settings.sampling_threshold:
        return df, False, None

    sampled = df.sample(n=min(settings.sample_size, n), shuffle=True, seed=settings.random_seed)
    return sampled, True, len(sampled)


def get_sample_info(n_rows: int) -> dict:
    will_sample = n_rows > settings.sampling_threshold
    return {
        "will_sample": will_sample,
        "original_rows": n_rows,
        "sample_rows": settings.sample_size if will_sample else n_rows,
        "threshold": settings.sampling_threshold,
    }
