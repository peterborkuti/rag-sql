import os
from pathlib import Path

class AppConfig:
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: str =os.path.join(PROJECT_ROOT, 'data')
    TEMPLATE_DIR: str =os.path.join(PROJECT_ROOT, 'templates')

