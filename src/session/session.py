import json
import os
import cv2

from datetime import datetime

from pandas import DataFrame
from strong_typing.serialization import object_to_json

from src.session.image_metadata import ImageMetadata

class FixedSizeMap:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.keys = []

    def add(self, key, entry):
        if len(self.map) >= self.capacity:
            oldest_key = self.keys.pop(0)
            del self.map[oldest_key]
        self.map[key] = entry
        self.keys.append(key)

    def update(self, key, entry):
        self.map[key] = entry
        self.keys.remove(key)
        self.keys.append(key)

    def get(self, key):
        return self.map.get(key)

    def remove(self, key):
        if key in self.map:
            del self.map[key]
            self.keys.remove(key)

    def __len__(self):
        return len(self.map)

class Session:
    def __init__(self, size, directory):
        self.cache = FixedSizeMap(size)
        now = datetime.now()
        self.session = now.strftime("%Y%d%m%H%M%S")

        self.session_dir = f"{directory}/{self.session}"
        self.image_dir = f"{self.session_dir}/images"
        self.metadata_dir = f"{self.session_dir}/metadata"
        os.mkdir(self.session_dir)
        os.mkdir(self.image_dir)
        os.mkdir(self.metadata_dir)

    def set_entry(self, track_id, score, clazz, img_width, img_height ):
        current_datetime = datetime.now()
        current_timestamp_ms = int(current_datetime.timestamp() * 1000)
        update_image = True
        current_entry = self.cache.get(track_id)
        if current_entry is None :
            current_entry = ImageMetadata(
                self.session,
                track_id, #image
                current_timestamp_ms,
                current_timestamp_ms,
                score,
                clazz,
                img_width,
                img_height )
            self.cache.add(track_id, current_entry)
        else :
            if score > current_entry.score :
                update_image = True
                new_entry = ImageMetadata(
                    current_entry.session,
                    current_entry.image,
                    current_entry.created,
                    current_timestamp_ms,
                    score,
                    current_entry.clazz,
                    img_width,
                    img_height)
                self.cache.update(track_id, new_entry)
            else :
                new_entry = ImageMetadata(
                    current_entry.session,
                    current_entry.image,
                    current_entry.created,
                    current_timestamp_ms,
                    current_entry.score,
                    current_entry.clazz,
                    current_entry.width,
                    current_entry.height)
                self.cache.update(track_id, new_entry)
        return update_image

    def save_image(self, track_id, img):
        cv2.imwrite(f"{self.image_dir}/{track_id}.jpg", img)

    def save_metadata(self, track_id) :
        entry = self.cache.get(track_id)
        if entry is not None:
            metadata_file = str(f"{self.metadata_dir}/{track_id}.json")
            with open(metadata_file, 'w') as file:
                file.write(json.dumps(object_to_json(entry)))
