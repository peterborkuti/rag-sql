import os
from pathlib import Path

from enum import Enum

# create an enum for the LLM types
class LLMType(str, Enum):
    LOCAL = 1
    GROQ = 2
    FAKE = 3

class AppConfig:
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: str =os.path.join(PROJECT_ROOT, 'data')
    TEMPLATE_DIR: str =os.path.join(PROJECT_ROOT, 'templates')
    CERT_DIR: str =os.path.join(PROJECT_ROOT, 'certs')
    LLM: LLMType = LLMType.FAKE
    LOCAL: bool = True

