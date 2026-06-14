from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "DAREEDA"
    app_version: str = "1.0.0"
    data_dir: Path = BASE_DIR / "data"
    reports_dir: Path = BASE_DIR / "reports"
    db_url: str = f"sqlite:///{BASE_DIR}/projects/dareeda.db"
    sampling_threshold: int = 100_000
    sample_size: int = 50_000
    random_seed: int = 42
    typst_bin: str = "typst"

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "projects").mkdir(parents=True, exist_ok=True)
