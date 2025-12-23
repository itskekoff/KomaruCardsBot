import sys
import toml
from loguru import logger

logger.remove()

try:
    config = toml.load("../config.toml")
    debug_logging = config.get("debug_logging", False)
except FileNotFoundError:
    debug_logging = False
except Exception as e:
    print(f"Error loading config.toml for logger: {e}. Defaulting to INFO level.")
    debug_logging = False

if debug_logging:
    log_level = "DEBUG"
else:
    log_level = "INFO"

logger.add(sys.stderr, level=log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

__all__ = ["logger"]
