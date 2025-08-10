import json
import os

from fsspec.utils import atomic_write
from strong_typing.serialization import object_to_json, json_to_object

from settings.settings import Settings


class SettingsDatabase :

    def __init__(self, path):
        self.path = path

        pass

    def write_settings(self, settings):
        with atomic_write(self.path, "w") as f:
            f.write(json.dumps(object_to_json(settings)))

    def read_settings(self) :
        try :
            with os.open(self.path, os.O_RDONLY) as f :
                json_str = os.read(f, os.path.getsize(self.path)).decode("utf-8")
                return json_to_object(Settings, json.loads(json_str))
        except Exception as e:
            return None






