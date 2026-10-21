import json
from typing import Dict, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.constants import BLOOD_GROUPS


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink"
    TEST_DATABASE_URL: str = "postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink_test"

    JWT_SECRET_KEY: str = "change-me-super-secret-key-bloodlink-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"

    # Business rules
    MIN_DONOR_AGE: int = 18
    MAX_DONOR_AGE: int = 65
    MIN_DONOR_WEIGHT_KG: float = 50.0
    MIN_DONATION_GAP_DAYS: int = 90
    BLOOD_SHELF_LIFE_DAYS: int = 42
    REGULAR_DONOR_MIN_DONATIONS: int = 3
    EXPIRY_ALERT_DAYS: int = 7

    # Prediction
    SAFE_MINIMUM_UNITS_DEFAULT: int = 10
    SAFE_MINIMUM_BY_GROUP: Union[str, Dict[str, int]] = "{}"
    PREDICTION_MIN_HISTORY_DAYS: int = 90
    PREDICTION_HOLDOUT_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def safe_minimums_dict(self) -> Dict[str, int]:
        overrides: Dict[str, int] = {}
        if isinstance(self.SAFE_MINIMUM_BY_GROUP, str):
            try:
                overrides = json.loads(self.SAFE_MINIMUM_BY_GROUP)
            except Exception:
                overrides = {}
        elif isinstance(self.SAFE_MINIMUM_BY_GROUP, dict):
            overrides = self.SAFE_MINIMUM_BY_GROUP

        result = {}
        for group in BLOOD_GROUPS:
            result[group] = int(overrides.get(group, self.SAFE_MINIMUM_UNITS_DEFAULT))
        return result

    def get_safe_minimum(self, blood_group: str) -> int:
        return self.safe_minimums_dict.get(blood_group, self.SAFE_MINIMUM_UNITS_DEFAULT)


settings = Settings()
