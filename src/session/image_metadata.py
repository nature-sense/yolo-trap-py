from dataclasses import dataclass
from datetime import datetime

from strong_typing.serialization import object_to_json

@dataclass
class ImageMetadata:
    session: str
    image: int
    created: int
    updated: int
    score: float
    clazz: int
    width: int
    height: int
