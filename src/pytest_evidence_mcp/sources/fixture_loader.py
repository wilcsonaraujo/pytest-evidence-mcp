import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None # type: ignore[assignment]
    YAML_AVAILABLE = False
    logger.debug("PyYAML not installed. YAML support disabled.")

def load_fixture(file_path: Path) -> tuple[Any | None, str | None]:
    """Loads a fixture file (JSON or YAML) and returns (data, error).
    
    NEVER raises an exception. ALL errors are converted into:
        - data = None
        - error = a descriptive string of the problem
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None, f"File not found: {file_path}"

    if not file_path.is_file():
        logger.warning(f"Path is not a file: {file_path}")
        return None, f"Path is not a file: {file_path}"

    extension = file_path.suffix.lower()

    if extension == ".json":
        return _load_json(file_path)
    elif extension in (".yaml", ".yml"):
        return _load_yaml(file_path)
    else:
        logger.warning(f"Unsupported file extension: {extension}")
        return None, f"Unsupported file extension: {extension}"


def _load_json(file_path: Path) -> tuple[Any | None, str | None]:
    """Load a JSON file"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        logger.debug(f"Successfully loaded JSON: {file_path}")
        return data, None
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON: {e}")
        return None, f"Invalid JSON: {e!s}"
    except UnicodeDecodeError as e:
        logger.warning(f"Invalid encoding: {e}")
        return None, f"Invalid encoding: {e!s}"
    except OSError as e:
        logger.error(f"Could not read file: {e}")
        return None, f"Could not read file: {e!s}"

def _load_yaml(file_path: Path) -> tuple[Any | None, str | None]:
    """Load a YAML file"""
    if not YAML_AVAILABLE:
        return None, "PyYAML not installed. Install with: pip install pyyaml"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        logger.debug(f"Successfully loaded YAML: {file_path}")
        return data, None
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML: {e}")
        return None, f"Invalid YAML: {e!s}"
    except UnicodeDecodeError as e:
        logger.warning(f"Invalid encoding: {e}")
        return None, f"Invalid encoding: {e!s}"
    except OSError as e:
        logger.error(f"Could not read file: {e}")
        return None, f"Could not read file: {e!s}"
