# Import configuration from parent config.py
import sys
from pathlib import Path

# Add parent directory to path to import config.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import directly from the config.py file to avoid circular imports
import importlib.util
spec = importlib.util.spec_from_file_location("config_module", parent_dir / "config.py")
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

config = config_module.config
logger = config_module.logger

__all__ = ['config', 'logger']
