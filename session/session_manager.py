import json
import os

from strong_typing.serialization import json_to_object

from session.image_metadata import ImageMetadata
from session.session import Session


class SessionManager:
    def __init__(self, max_sessions, cache_size, directory):
        self.max_sessions = max_sessions
        self.cache_size = cache_size
        self.directory = directory

    def new_session(self):
        self.clean_up_sessions()
        return Session(self.cache_size, self.directory)

    def clean_up_sessions(self):
        sessions = sorted(os.listdir(self.directory))
        num_sessions = len(sessions)
        print(f"num sesions {num_sessions} max sessions {self.max_sessions}")
        if num_sessions >= self.max_sessions:
            for x in range(0, num_sessions-self.max_sessions+1):
                sess_path = f"{self.directory}/{sessions[x]}"
                img_path = f"{sess_path}/images"
                self.delete_directory(img_path)
                meta_path = f"{sess_path}/metadata"
                self.delete_directory(meta_path)
                os.rmdir(sess_path)

    def delete_directory(self, dir_path):
        print(dir_path)
        if not os.path.exists(dir_path):
            print(f"Directory not found: {dir_path}")
            return

        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                print("Deleting file", file_path)
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        os.rmdir(dir_path)

    def list_sessions(self):
        return sorted(os.listdir(self.directory))

    

    def list_images_for_session(self, session):
        image_path = f"{self.directory}/{session}/images"
        metadata_path = f"{self.directory}/{session}/metadata"
        if not os.path.exists(image_path):
            print(f"Directory not found: {image_path}")
            return []
        if not os.path.exists(metadata_path):
            print(f"Directory not found: {metadata_path}")
            return []
        # Get the list of image files with the file extension removed
        return map(lambda img : img.split(".")[0],sorted(os.listdir(image_path)))

    def get_image_data(self, session, image):
        image_path =   f"{self.directory}/{session}/images/{image}.jpg"
        metadata_path = f"{self.directory}/{session}/metadata/{image}.json"
        assert(os.path.exists(metadata_path))
        assert(os.path.exists(image_path))

        m_fd = os.open(metadata_path, os.O_RDONLY)
        json_str = os.read(m_fd, os.path.getsize(metadata_path)).decode("utf-8")
        json_map = json.loads(json_str)
        imd = json_to_object(ImageMetadata, json_map)

        i_fd = os.open(image_path, os.O_RDONLY)
        img = os.read(i_fd, os.path.getsize(image_path))

        return imd, img











