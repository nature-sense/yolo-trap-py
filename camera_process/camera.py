from abc import ABC, abstractmethod

from picamera2 import Picamera2


class Camera(ABC) :
    def __init__(self):
        self.picam2 = None

    @abstractmethod
    def setup(self, picam2, camera_config) :
        pass

    @abstractmethod
    async def control(self, msg):
        pass