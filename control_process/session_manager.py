#!/usr/bin/env python
"""
Session Server

Used by the Bluetooth Control process to manage the image and metadata files.
The server receives messages from the detect-flow process via a TCP socket, creates and
modifies directories and files accordingly, and maintains a metadata cache, which allows
state to be queried and notified ia the Bluetooth interface
"""
__author__ = "Steve"
__contact__ = "steve@naturesense.io"
__copyright__ = "Copyright 2025, NatureSense"

import json
import os
from datetime import datetime

import cv2

import picologging as logging

from strong_typing.serialization import json_to_object
from strong_typing.serializer import object_to_json

from control_process.bluetooth_controller import BluetoothController
from ipc.active_flow import ActiveFlow
from ipc.detection_metadata import DetectionMetadata
from ipc.ipc import IpcServer
from ipc.session_messages import SessionMessage, MsgType

STORAGE_DIRECTORY = "/media/usb1"
SESSIONS_DIRECTORY = STORAGE_DIRECTORY +"/sessions"

session_format = "%Y%m%d$H%M%S"
def session_to_datetime(session) :
    return datetime.strptime(session,session_format)

class SessionCache:
    def __init__(self) :
        self.sessions = {}

    def new_session(self, session) :
        self.sessions[session] = {}

    def delete_session(self, session) :
        del self.sessions[session]

    def new_detection(self, session, detection_metadata) :
       sess = self.sessions.get(session)
       if sess is not None :
           sess[detection_metadata.detection] = detection_metadata

    def count_detections(self, session) :
        return len(self.sessions.get(session))

    def get_detection(self, session, detection ):
        sess = self.sessions.get(session)
        if sess is not None :
            meta = sess.get(detection)
            if meta is not None :
                return meta
        return None

    def set_detection(self, session, detection_metadata) :
        sess = self.sessions.get(session)
        if sess is not None:
            sess[detection_metadata.detection] = detection_metadata

    def list_sessions(self) :
        return map(lambda session : (session, len(self.sessions[session])), sorted(self.sessions.keys()))

    def get_detections_for_session(self, session):
        return self.sessions.get(session)

class SessionManager:
    def __init__(self, settings_manager): #, control_service):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(name=__name__)
        self.session_cache = SessionCache()
        
        self.ipc_server = IpcServer(self)
        self.bluetooth_controller = BluetoothController(self, self.ipc_server)
        
        self.max_sessions = settings_manager.get_settings().max_sessions
        #self.control_service = control_service

        self.current_session = None
        self.session_dir = None
        self.image_dir = None
        self.metadata_dir = None

        #self.check_storage()


    def check_storage(self):
        logging.debug("Checking storage")

        if os.path.exists(STORAGE_DIRECTORY) :
            if not os.path.exists(SESSIONS_DIRECTORY):
                os.makedirs(SESSIONS_DIRECTORY)
            self.build_cache()
            logging.debug("Storage found")
            self.bluetooth_controller.state_controller.set_storage_state(True)
        else:
            logging.debug("No storage found")
            self.bluetooth_controller.state_controller.set_storage_state(False)

    def build_cache(self):
        """
        build_cache()

        Rebuild the session cache on startup by scanning session directories
        and reading the image metadata
        """
        self.logger.debug("Rebuilding sessions cache....")
        sessions = sorted(os.listdir(SESSIONS_DIRECTORY))
        for session in sessions:
            logging.debug(f"Found {session}")
            self.session_cache.new_session(session)
            detections = self._get_detections_metadata_for_session(session)
            for detection in detections:
                logging.debug(f"Found image {detection.detection}")
                self.session_cache.new_detection(session, detection)

    async def handle_message(self, proto):
        """
           handle_message()

           handle session messages received on the IPC socket
           Messages are:
               NEW_SESSION
               NEW_DETECTION
               UPDATE_DETECTION_META
               UPDATE_DETECTION
               PREVIEW_FRAME

        """

        type, msg = SessionMessage.from_proto(proto)
        logging.debug(f"Got message {type}")

        # ==================================================================
        # NEW_SESSION
        # 1. Create the directory structure for the session
        # 2. Set it to be the currently active session
        # 3. Add an entry to the sessions cache
        # 4. Purge old sessions if the number now exceeds max-sessions
        # ==================================================================

        if type == MsgType.NEW_SESSION :
            logging.debug("Received NEW_SESSION")

            # Create the directories and an entry in the cache
            self.current_session = msg.session
            self.session_dir = f"{SESSIONS_DIRECTORY}/{msg.session}"
            self.image_dir = f"{self.session_dir}/images"
            self.metadata_dir = f"{self.session_dir}/metadata"

            os.mkdir(self.session_dir)
            os.mkdir(self.image_dir)
            os.mkdir(self.metadata_dir)

            logging.debug("Created directories")

            self.session_cache.new_session(msg.session)
            await self.bluetooth_controller.session_notifier.notify_new_session(self.current_session)
            await self._clean_up_sessions()

            logging.debug("New session complete")


        # ==================================================================
        # NEW_DETECTION
        # 1. Create the DetectionMetadata object and write the metadata json file
        # 2. Write the immage jpeg file
        # 3. Update the session cache by adding the detection to the session
        # ==================================================================
        elif type == MsgType.NEW_DETECTION :
            logging.debug("**** Received NEW_DETECTION ****")

            metadata = DetectionMetadata(
                self.current_session,
                msg.detection,
                msg.created,
                msg.created, #updated
                msg.score,
                msg.clazz,
                msg.width,
                msg.height,
            )

            metadata_file = str(f"{self.metadata_dir}/{msg.detection}.json")
            image_file = str(f"{self.image_dir}/{msg.detection}.jpg")

            with open(metadata_file, 'w') as file:
                file.write(json.dumps(object_to_json(metadata)))
            with open(image_file, 'wb') as file:
                file.write(msg.img_data)

            self.session_cache.new_detection(self.current_session, metadata)
            await self.bluetooth_controller.session_notifier.notify_session_details(
                self.current_session,
                self.session_cache.count_detections(self.current_session)
            )
            await self.bluetooth_controller.detection_notifier.notify_detection_meta(metadata)

        # ==================================================================
        # UPDATE_DETECTION_META
        # 1. Update the metadata in the cache
        # 2. Overwrite the data in the metadata file
        # ==================================================================
        elif type == MsgType.UPDATE_DETECTION_META :
            meta = self.session_cache.get_detection(self.current_session, msg.detection)
            if meta is not None :
                meta.updated = msg.updated
                self.session_cache.set_detection(self.current_session, meta)
                metadata_file = str(f"{self.metadata_dir}/{meta.detection}.json")
                with open(metadata_file, 'w') as file:
                    try :
                        file.write(json.dumps(object_to_json(meta)))
                    except :
                        logging.debug("Failed to save metadata")

        # ==================================================================
        # UPDATE_DETECTION
        # 1. Update the metadata in the cache
        # 2. Overwrite the data in the metadata file
        # 3. Overwrite the image in the image file
        # ==================================================================
        elif type == MsgType.UPDATE_DETECTION :
            meta = self.session_cache.get_detection(self.current_session, msg.detection)
            if meta is not None:
                meta.updated = msg.updated
                meta.score = msg.score
                meta.width = msg.width
                meta.height = msg.height

                self.session_cache.set_detection(self.current_session, meta)

                metadata_file = str(f"{self.metadata_dir}/{msg.detection}.json")
                with open(metadata_file, 'w') as file:
                    file.write(json.dumps(object_to_json(meta)))
                try:
                    cv2.imwrite(f"{self.image_dir}/{msg.detection}.jpg", msg.img_data)
                except:
                    logging.debug("Failed to save image")

        # ==================================================================
        # PREVIEW_FRAME
        # ==================================================================
        elif type == MsgType.STREAM_FRAME :
            logging.debug("Got frame - sending it to image streamer")
            await self.bluetooth_controller.image_streamer.addFrame(msg.timestamp, msg.frame)

        # ==================================================================
        # STORAGE
        # ==================================================================
        elif type == MsgType.STORAGE :
            logging.debug(f"Storage message - state = {msg.mounted}")
            self.bluetooth_controller.state_controller.set_storage_state(msg.mounted)

        # ==================================================================
        # STORAGE
        # ==================================================================
        elif type == MsgType.ACTIVE_FLOW :
            logging.debug(f"Flow state message flow = ${ActiveFlow(msg.flow)}")
            self.bluetooth_controller.state_controller.set_active_flow(ActiveFlow(msg.flow))

        # Ignore unknown
        else :
            pass

    def list_sessions(self):
        return self.session_cache.list_sessions()

    def list_detections_for_session(self, session):
        return self.session_cache.get_detections_for_session(session)

    async def _clean_up_sessions(self):
        session_files = os.listdir(SESSIONS_DIRECTORY)
        sessions = sorted(session_files)
        num_sessions = len(sessions)
        logging.debug(f"num sessions {num_sessions} max sessions {self.max_sessions}")
        if num_sessions >= self.max_sessions:
            #for idx in range(0, num_sessions-self.max_sessions+1):
            for idx in range(0, num_sessions - self.max_sessions+1):

                sess_path = f"{SESSIONS_DIRECTORY}/{sessions[idx]}"
                img_path = f"{sess_path}/images"
                self._delete_session_files(img_path)
                meta_path = f"{sess_path}/metadata"
                self._delete_session_files(meta_path)
                os.rmdir(sess_path)
                self.session_cache.delete_session(sessions[idx])
                await self.bluetooth_controller.session_notifier.notify_delete_session(sessions[idx])

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
        metadata_path = f"{SESSIONS_DIRECTORY}/{session}/metadata"
        files = sorted(os.listdir(metadata_path))
        for file in files:
            file_path = f"{metadata_path}/{file}"
            m_fd = os.open(file_path, os.O_RDONLY)
            json_str = os.read(m_fd, os.path.getsize(file_path)).decode("utf-8")
            metadata_list.append(json_to_object(DetectionMetadata, json.loads(json_str)))
        return metadata_list


    def list_images_for_session(self, session):
        image_path = f"{SESSIONS_DIRECTORY}/{session}/images"
        metadata_path = f"{SESSIONS_DIRECTORY}/{session}/metadata"
        if not os.path.exists(image_path):
            logging.debug(f"Directory not found: {image_path}")
            return []
        if not os.path.exists(metadata_path):
            logging.debug(f"Directory not found: {metadata_path}")
            return []
        # Get the list of image files with the file extension removed
        return map(lambda img : img.split(".")[0],sorted(os.listdir(image_path)))

    def get_image_data(self, session, image):
        image_path =   f"{SESSIONS_DIRECTORY}/{session}/images/{image}.jpg"
        metadata_path = f"{SESSIONS_DIRECTORY}/{session}/metadata/{image}.json"
        assert(os.path.exists(metadata_path))
        assert(os.path.exists(image_path))

        m_fd = os.open(metadata_path, os.O_RDONLY)
        json_str = os.read(m_fd, os.path.getsize(metadata_path)).decode("utf-8")
        json_map = json.loads(json_str)
        imd = json_to_object(DetectionMetadata, json_map)

        i_fd = os.open(image_path, os.O_RDONLY)
        img = os.read(i_fd, os.path.getsize(image_path))

        return imd, img











