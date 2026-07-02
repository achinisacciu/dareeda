from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "DAREEDA"
    app_version: str = "1.0.0"
    data_dir: Path = BASE_DIR / "data"
    reports_dir: Path = BASE_DIR / "reports"
    sampling_threshold: int = 100_000
    sample_size: int = 50_000
    random_seed: int = 42
    typst_bin: str = "typst"

    # Operational limits (config-driven instead of hardcoded)
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB
    # ponytail: list[str] nativo, non .split(",") che non copre 127.0.0.1
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    upload_ttl_minutes: int = 30

    # Module-level limits (replaces magic numbers in eda/modules/*.py)
    ml_max_features_mutual_info: int = 15
    ml_max_features_clustering: int = 8
    ml_max_features_anomaly: int = 10
    ml_max_features_corr_pairs: int = 20
    ml_max_features_corr_global: int = 25
    ml_max_features_pca: int = 20
    ml_max_corr_pairs_return: int = 15
    ml_univariate_top_n: int = 5000


def _init_dirs() -> None:
    """Crea le directory di servizio una sola volta, senza side-effect a import-time."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "projects").mkdir(parents=True, exist_ok=True)


settings = Settings()
