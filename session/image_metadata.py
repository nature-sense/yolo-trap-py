from dataclasses import dataclass

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
