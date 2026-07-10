from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class EngineInfo:
    id: str
    name: str
    description: str


class OCREngine(ABC):
    info: EngineInfo

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        pass
