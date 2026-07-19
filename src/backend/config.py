"""Environment configuration for the application."""

from __future__ import annotations

import os


class Settings:
    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.log_level = os.getenv("LOG_LEVEL", "info")
        self.frontend_dist = os.getenv("FRONTEND_DIST", "")


settings = Settings()
