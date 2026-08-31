from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Vitalis API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Seguimiento de recomendaciones: días que la persona debe sostener una
    # actividad del plan antes de que se marque como completada.
    SEGUIMIENTO_DIAS_OBJETIVO: int = 21   # por defecto, si la ficha no trae uno propio
    SEGUIMIENTO_DIAS_PRUEBA: int = 0      # >0 activa "modo prueba": TODAS las actividades usan este nº

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=True,
    )


settings = Settings()