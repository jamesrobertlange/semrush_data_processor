from dataclasses import dataclass


@dataclass
class AppConfig:
    MAX_FILE_SIZE_MB: int = 999999
    MAX_WORKERS: int = 3
    PREVIEW_ROWS: int = 10


config = AppConfig()
