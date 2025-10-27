"""Configuration loader for YAML settings."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class AnkiConfig:
    """Anki connection configuration."""

    connect_url: str
    connect_timeout: int
    retry_attempts: int


@dataclass
class TutorConfig:
    """AI tutor configuration."""

    personalities: list[dict[str, Any]]
    modes: dict[str, Any]


@dataclass
class LearningConfig:
    """Learning and evaluation configuration."""

    simple_srs: dict[str, bool]
    evaluation: dict[str, bool]


@dataclass
class StorageConfig:
    """Storage paths and settings."""

    data_dir: str
    sessions_dir: str
    progress_dir: str
    backup_enabled: bool


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str
    format: str


@dataclass
class Config:
    """Complete application configuration."""

    anki: AnkiConfig
    tutor: TutorConfig
    learning: LearningConfig
    storage: StorageConfig
    logging: LoggingConfig


class ConfigLoader:
    """Load and validate YAML configuration."""

    @staticmethod
    def load(config_path: Path | str = "config.yaml") -> Config:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Validated Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.info(f"Loading configuration from {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        try:
            config = Config(
                anki=AnkiConfig(**data["anki"]),
                tutor=TutorConfig(**data["tutor"]),
                learning=LearningConfig(**data["learning"]),
                storage=StorageConfig(**data["storage"]),
                logging=LoggingConfig(**data["logging"]),
            )
            logger.info("Configuration loaded successfully")
            return config
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid configuration: {e}") from e

    @staticmethod
    def create_default(config_path: Path | str = "config.yaml") -> None:
        """Create a default configuration file.

        Args:
            config_path: Path where to create the config file
        """
        default_config = {
            "anki": {
                "connect_url": "http://localhost:8765",
                "connect_timeout": 30,
                "retry_attempts": 3,
            },
            "tutor": {
                "personalities": [
                    {"type": "normal", "weight": 3},
                    {"type": "pirate", "weight": 1},
                ],
                "modes": {
                    "explain": {"enabled": True, "max_sentences": 5},
                    "test": {"enabled": True, "show_correct_answer": True},
                },
            },
            "learning": {
                "simple_srs": {"retry_incorrect": True, "shuffle_cards": False},
                "evaluation": {
                    "case_sensitive": False,
                    "whitespace_sensitive": False,
                    "require_user_review": True,
                },
            },
            "storage": {
                "data_dir": "./data",
                "sessions_dir": "./data/sessions",
                "progress_dir": "./data/progress",
                "backup_enabled": True,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        config_path = Path(config_path)
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Default configuration created at {config_path}")
