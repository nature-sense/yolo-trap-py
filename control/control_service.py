import asyncio
import logging
import math
import os
from multiprocessing import Process
from typing import Any

from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

from control.bluetooth_messages import (
    SessionDetailsMessage,
    ImageHeaderMessage,
    ImageSegmentMessage,
    DetectionReferenceMessage, NewSessionMessage, DeleteSessionMessage,
)

from session.session_service import SessionService

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
MAX_SESSIONS = 3
MIN_SCORE = 0.5

IMAGE_SEGMENT = 200

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)

SERVICE_UUID    = "213e313b-d0df-4350-8e5d-ae657962bb56"
STATE_UUID      = "f4a6c1ed-86ff-4c01-932f-7c810dc66b43"
IMAGE_UUID      = "8029922b-2e7e-4a16-8794-f74fc4915d16"
SESSION_LIST_REQ_UUID = "c254eaaf-a9f3-4823-a022-1d817a11de07"
SESSION_NOTIF_UUID = "1319bc48-793d-4bb0-a4c6-d5001c629651"
SESSION_DETAILS_REQ_UUID = "5b56f92a-f283-4711-9787-97df31f48991"
 #= "3b3a7400-681b-42ea-8202-8437057e7f1c"

IMAGE_DETAILS_REQ_UUID = "f59cef6f-8af1-4636-ad8a-23cb2e12da5d"
IMAGE_DETAILS_UUID = "8bf01881-cfbe-48b2-aca6-f7f25c796943"

class SessionNotifier :
    def __init__(self, bluetooth_server):
        self.bluetooth_server = bluetooth_server
        self.notif_queue = asyncio.Queue()
        self.tasks = set()
        self.logger = logging.getLogger(name=__name__)


    async def start(self) :
        task = asyncio.create_task(self.publish())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def notify_new_session(self, session)  :
        msg = NewSessionMessage(session).to_proto()
        await self.notif_queue.put(msg)

    async def notify_delete_session(self, session) :
        msg = DeleteSessionMessage(session).to_proto()
        await self.notif_queue.put(msg)

    async def notify_session_details(self, session, detections):
        msg = SessionDetailsMessage(session, detections).to_proto()
        await self.notif_queue.put(msg)

    async def publish(self) :
        characteristic = self.bluetooth_server.get_characteristic(SESSION_NOTIF_UUID)

        while True:
            msg = await self.notif_queue.get()
            characteristic.value = msg
            result = self.bluetooth_server.update_value(SERVICE_UUID, SESSION_NOTIF_UUID)
            self.logger.debug(f"Notify result = {result}")


class ControlService:
    def __init__(self, detector) -> None:
        logging.basicConfig(level=logging.DEBUG)

        self.trigger = asyncio.Event()
        self.logger = logging.getLogger(name=__name__)
        self.detector = detector
        self.session_server = None
        self.process = None
        self.bluetooth_server = None
        self.session_notifier = None

        self.node_name = os.uname().nodename.upper()
        self.background_tasks = set()
        self.session_notifs = asyncio.Queue()


    async def run(self, loop):
        self.trigger.clear()

        # Instantiate the server
        service_name = self.node_name
        self.bluetooth_server = BlessServer(name=service_name, loop=loop)
        self.bluetooth_server.read_request_func = self.read_request
        self.bluetooth_server.write_request_func = self.write_request
        self.session_notifier = SessionNotifier(self.bluetooth_server)
        self.session_server = SessionService(MAX_SESSIONS, SESSIONS_DIRECTORY, self)

        # Add Service
        await self.bluetooth_server.add_new_service(SERVICE_UUID)
        await self.add_read_write_char(STATE_UUID, bin(0))
        await self.add_read_write_char(SESSION_LIST_REQ_UUID, bin(0))
        await self.add_write_char(SESSION_DETAILS_REQ_UUID, bin(0))
        await self.add_write_char(IMAGE_DETAILS_REQ_UUID, bin(0))
        #await self.add_notif_char(SESSION_LIST_ENTRY_UUID, bin(0))
        await self.add_notif_char(SESSION_NOTIF_UUID, bin(0))
        await self.add_notif_char(IMAGE_DETAILS_UUID, bin(0))

        await self.session_notifier.start()
        await self.session_server.start_service()
        await self.bluetooth_server.start()


        self.logger.debug("Advertising")
        await self.trigger.wait()

    def read_request(self, characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        self.logger.debug(f"Reading {characteristic.value}")
        if characteristic.uuid == SESSION_LIST_REQ_UUID:
            self.session_list()
            return characteristic.value
        else:
            return characteristic.value

    def write_request(self, characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        if characteristic.uuid == STATE_UUID:
            self.change_state(characteristic, value)
            
        elif characteristic.uuid == SESSION_LIST_REQ_UUID:
            self.logger.debug("Request session list")
            task = asyncio.create_task(self.session_list())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
            
        #elif characteristic.uuid == SESSION_DETAILS_REQ_UUID:
        #    session = SessionReference.from_proto(value).session
        #    #session = value.decode("utf-8")
        #    self.logger.debug("Request details for session " + session)
        #    task = asyncio.create_task(self.image_list(session))
        #    self.background_tasks.add(task)
        #    task.add_done_callback(self.background_tasks.discard)
            
        #elif characteristic.uuid == IMAGE_DETAILS_REQ_UUID:
        #    image_ref = DetectionReference.from_proto(value)
        #    self.logger.debug(f"Request details for image " + image_ref.session + " " + image_ref.image)
        #    task = asyncio.create_task(self.image_details(image_ref))
        #    self.background_tasks.add(task)
        #    task.add_done_callback(self.background_tasks.discard)


    def change_state(self, characteristic, value):
        old_state = characteristic.value[0] == 1
        new_state = value[0] == 1
        self.logger.debug(f"Change state - old = {old_state} new = {new_state}")

        if old_state != new_state:
            characteristic.value = value

            if new_state is True:
                self.process = Process(target=self.detector, args=())
                self.process.start()
            else:
                self.process.terminate()

            #characteristic.update()
            self.logger.debug(f"State set to {characteristic.value}")

    async def session_list(self):
        self.logger.debug("Session list")
        sessions = self.session_server.list_sessions()
        for session in sessions:
            self.logger.debug(f"Updating Session = {session}")
            await self.session_notifier.notify_session_details(session[0], session[1])


    #async def image_list(self, session):
    #    images = self.session_server.list_images_for_session(session)
    #    session_details_char = self.bluetooth_server.get_characteristic(SESSION_DETAILS_UUID)

    #    for image in images:
    #        session_details_char.value = DetectionReferenceMessage(session, image).to_proto()

    #        self.logger.debug(f"Image {image}")
    #        result = self.bluetooth_server.update_value(SERVICE_UUID, SESSION_DETAILS_UUID)
    #        self.logger.debug(f"result = {result}")

    async def image_details(self, image_ref):
        image_details_char = self.bluetooth_server.get_characteristic(IMAGE_DETAILS_UUID)
        meta, img = self.session_server.get_image_data(image_ref.session, image_ref.image)
        segments = math.ceil(len(img)/IMAGE_SEGMENT)

        image_details_char.value = ImageHeaderMessage(meta, segments).to_proto()
        result = self.bluetooth_server.update_value(SERVICE_UUID, IMAGE_DETAILS_UUID)
        self.logger.debug(f"result = {result}")

        start_index = 0
        segment = 1
        while start_index < len(img) :
            img_seg = img[start_index:start_index+IMAGE_SEGMENT]
            image_details_char.value = ImageSegmentMessage(segment, img_seg).to_proto()
            segment = segment+1
            start_index = start_index + IMAGE_SEGMENT
            result = self.bluetooth_server.update_value(SERVICE_UUID, IMAGE_DETAILS_UUID)
            self.logger.debug(f"result = {result}")
        if start_index != len(img) :
            segment = segment + 1
            img_seg = img[start_index:]
            image_details_char.value = ImageSegmentMessage(segment, img_seg )
            result = self.bluetooth_server.update_value(SERVICE_UUID, IMAGE_DETAILS_UUID)
            self.logger.debug(f"result = {result}")
        self.logger.debug(f"last segment = {segment}")

    async def add_read_write_char(self, uuid, value):
        # Add a Characteristic to the service
        char_flags = GATTCharacteristicProperties.read | GATTCharacteristicProperties.write
        permissions = GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        return await self.bluetooth_server.add_new_characteristic(
            service_uuid=SERVICE_UUID,
            char_uuid=uuid,
            properties=char_flags,
            value=value.encode(),
            permissions=permissions
        )

    async def add_write_char(self, uuid, value):
        char_flags = GATTCharacteristicProperties.write
        permissions = GATTAttributePermissions.writeable
        return await self.bluetooth_server.add_new_characteristic(
            service_uuid= SERVICE_UUID,
            char_uuid=uuid,
            properties=char_flags,
            value=value.encode(),
            permissions=permissions
        )

    async def add_notif_char(self, uuid, value):
        char_flags = (
                GATTCharacteristicProperties.notify |
                GATTCharacteristicProperties.indicate |
                GATTCharacteristicProperties.read
        )
        permissions = GATTAttributePermissions.writeable
        return await self.bluetooth_server.add_new_characteristic(
             service_uuid=SERVICE_UUID,
            char_uuid=uuid,
            properties=char_flags,
            value=value.encode(),
            permissions=permissions
        )


