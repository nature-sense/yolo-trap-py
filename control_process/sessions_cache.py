import json
import logging
import os

import cv2
from aioreactive import AsyncSubject
from strong_typing.serialization import json_to_object, object_to_json

from ipc.detection_metadata import DetectionMetadata


class SessionsCache:
    def __init__(self, sessions_directory, settings_manager) :
        self.sessions_directory = sessions_directory
        self.settings_manager = settings_manager
        self.sessions = {}
        self.current_session = None

        self.new_session_stream = AsyncSubject()
        self.del_session_stream = AsyncSubject()
        self.session_details_stream = AsyncSubject()
        self.new_detection_stream = AsyncSubject()

    async def new_session(self, session) :
        # Create the directories and an entry in the cache
        self.current_session = session

        session_dir = f"{self.sessions_directory}/{session}"
        image_dir = f"{session_dir}/images"
        metadata_dir = f"{session_dir}/metadata"

        os.mkdir(session_dir)
        os.mkdir(image_dir)
        os.mkdir(metadata_dir)

        logging.debug("Created directories")

        await self._new_session(session)
        await self._clean_up_sessions()

    async def  new_detection(self, metadata, image) :
        session_dir = f"{self.sessions_directory}/{metadata.session}"

        metadata_file = str(f"{session_dir}/metadata/{metadata.detection}.json")
        image_file = str(f"{session_dir}/images/{metadata.detection}.jpg")

        with open(metadata_file, 'w') as file:
            file.write(json.dumps(object_to_json(metadata)))
        with open(image_file, 'wb') as file:
            file.write(image)

        await self._new_detection(metadata.session, metadata, image)

    async def update_detection_meta(self,  detection, updated) :
        meta = self._get_detection(self.current_session, detection)
        if meta is not None :
            session_dir = f"{self.sessions_directory}/{self.current_session}"
            meta.updated = updated
            self._set_detection(self.current_session, meta)
            metadata_file = str(f"{session_dir}/metadata/{meta.detection}.json")
            with open(metadata_file, 'w') as file:
                try :
                    file.write(json.dumps(object_to_json(meta)))
                except :
                    logging.debug("Failed to save metadata")

    async def update_detection(self,  detection, updated, score, width, height, img_data):

        meta = self._get_detection(self.current_session, detection)
        if meta is not None:
            meta.updated = updated
            meta.score = score
            meta.width = width
            meta.height = height

            self._set_detection(self.current_session, meta)

            session_dir = f"{self.sessions_directory}/{self.current_session}"

            metadata_file = str(f"{session_dir}/metadata/{meta.detection}.json")
            with open(metadata_file, 'w') as file:
                file.write(json.dumps(object_to_json(meta)))
            try:
                cv2.imwrite(f"{session_dir}/images/{meta.detection}.jpg", img_data)
            except:
                logging.debug("Failed to save image")

    def list_sessions(self):
        return map(lambda session: (session, len(self.sessions[session])), sorted(self.sessions.keys()))

    def get_detections_for_session(self, session):
        detections = []
        for det in self.sessions.get(session).values():
            img = self._get_image_data(session, det.detection)
            detections.append((det, img))
        return detections

    async def init(self) :
        logging.debug("Rebuilding sessions cache....")
        sessions = sorted(os.listdir(self.sessions_directory))
        for session in sessions:
            logging.debug(f"Found {session}")
            await self._new_session(session)
            detections = self._get_detections_metadata_for_session(session)
            for detection in detections:
                logging.debug(f"detection image {detection.detection}")
                await self._init_detection(session, detection)

    async def _new_session(self, session) :
        self.sessions[session] = {}
        await self.new_session_stream.asend(session)

    async def _delete_session(self, session) :
        del self.sessions[session]
        await self.del_session_stream.asend(session)

    async def _new_detection(self, session, detection_metadata, image) :
       sess = self.sessions.get(session)
       if sess is not None :
            sess[detection_metadata.detection] = detection_metadata
            await self.new_detection_stream.asend((detection_metadata, image))
            await self.session_details_stream.asend((session, len(self.sessions.get(session))))

    async def _init_detection(self, session, detection_metadata) :
       sess = self.sessions.get(session)
       if sess is not None :
            sess[detection_metadata.detection] = detection_metadata

    def _count_detections(self, session) :
        return len(self.sessions.get(session))

    def _get_detection(self, session, detection):
        sess = self.sessions.get(session)
        if sess is not None :
            meta = sess.get(detection)
            if meta is not None :
                return meta
        return None

    def _set_detection(self, session, metadata) :
        sess = self.sessions.get(session)
        if sess is not None:
            sess[metadata.detection] = metadata


    async def _clean_up_sessions(self):
        settings = self.settings_manager.get_settings()
        max_sessions = settings.max_sessions
        session_files = os.listdir(self.sessions_directory)
        sessions = sorted(session_files)
        num_sessions = len(sessions)
        logging.debug(f"num sessions {num_sessions} max sessions {max_sessions}")
        if num_sessions >= max_sessions:
            #for idx in range(0, num_sessions-self.max_sessions+1):
            for idx in range(0, num_sessions - max_sessions):

                sess_path = f"{self.sessions_directory}/{sessions[idx]}"
                img_path = f"{sess_path}/images"
                self._delete_session_files(img_path)
                meta_path = f"{sess_path}/metadata"
                self._delete_session_files(meta_path)
                os.rmdir(sess_path)
                await self._delete_session(sessions[idx])

                #resp = SessionDeletedResponse(sessions[idx]).to_proto()
                #await self.websocket_server.send_response(resp)

    def _delete_session_files(self, dir_path):
        print(dir_path)
        if not os.path.exists(dir_path):
            logging.debug(f"Directory not found: {dir_path}")
            return

        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                logging.debug(f"Deleting file {file_path}")
                os.remove(file_path)
            except Exception as e:
                logging.debug(f"Error deleting {file_path}: {e}")
        os.rmdir(dir_path)

    def _get_detections_metadata_for_session(self, session) :
        metadata_list = []
        metadata_path = f"{self.sessions_directory}/{session}/metadata"
        files = sorted(os.listdir(metadata_path))
        for file in files:
            file_path = f"{metadata_path}/{file}"
            m_fd = os.open(file_path, os.O_RDONLY)
            try :
                json_str = os.read(m_fd, os.path.getsize(file_path)).decode("utf-8")
                metadata_list.append(json_to_object(DetectionMetadata, json.loads(json_str)))
            except Exception as e :
                logging.error(f"Error reading metadate file {file_path}: {e}")

        return metadata_list

    def _get_image_data(self, session, detection):
        image_path =   f"{self.sessions_directory}/{session}/images/{detection}.jpg"
        assert(os.path.exists(image_path))

        i_fd = os.open(image_path, os.O_RDONLY)
        img = os.read(i_fd, os.path.getsize(image_path))

        return img
