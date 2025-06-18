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
    DetectionReferenceMessage,
    DetectionsForSessionMessage,
)

from control.notifiers.detection_notifier import DetectionNotifier
from control.notifiers.image_sender import ImageSender
from control.notifiers.image_streamer import ImageStreamer
from control.notifiers.session_notifier import SessionNotifier
from control.uuids import SERVICE_UUID, SESSION_LIST_REQ_UUID, SESSION_NOTIF_UUID, DETECTIONS_LIST_REQ_UUID, \
    DETECTION_NOTIF_UUID, IMAGE_REQ_UUID, IMAGE_SEGMENT_UUID, PREVIEW_STREAM_UUID, FLOW_UUID

from session.session_service import SessionService

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
MAX_SESSIONS = 3
MIN_SCORE = 0.5

NO_FLOW = 0
DETECT_FLOW = 1
PREVIEW_FLOW = 2

IMAGE_SEGMENT = 200

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)


class ControlService:
    def __init__(self, detector, previewer) -> None:
        logging.basicConfig(level=logging.DEBUG)

        self.trigger = asyncio.Event()
        self.logger = logging.getLogger(name=__name__)
        self.detector = detector # detector flow
        self.previewer = previewer # preview flow

        self.session_server = None
        self.process = None
        self.bluetooth_server = None
        self.session_notifier = None
        self.detection_notifier = None
        self.image_sender = None
        self.image_streamer = None
        self.active_flow = NO_FLOW

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
        self.detection_notifier = DetectionNotifier(self.bluetooth_server)
        self.image_sender = ImageSender(self.bluetooth_server)
        self.image_streamer = ImageStreamer(self.bluetooth_server)
        self.session_server = SessionService(MAX_SESSIONS, SESSIONS_DIRECTORY, self)

        # Add Service
        await self.bluetooth_server.add_new_service(SERVICE_UUID)
        await self.add_read_write_char(FLOW_UUID, bin(0))
        await self.add_notif_char(PREVIEW_STREAM_UUID, bin(0)),

        await self.add_read_write_char(SESSION_LIST_REQ_UUID, bin(0))
        await self.add_notif_char(SESSION_NOTIF_UUID, bin(0))

        await self.add_read_write_char(DETECTIONS_LIST_REQ_UUID, bin(0))
        await self.add_notif_char(DETECTION_NOTIF_UUID, bin(0))

        await self.add_read_write_char(IMAGE_REQ_UUID, bin(0))
        await self.add_notif_char(IMAGE_SEGMENT_UUID, bin(0))

        await self.session_notifier.start()
        await self.detection_notifier.start()
        await self.image_sender.start()
        await self.image_streamer.start()
        await self.session_server.start_service()
        await self.bluetooth_server.start()

        self.logger.debug("Advertising")
        await self.trigger.wait()

    def read_request(self, characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        self.logger.debug(f"Reading {characteristic.value}")
        if characteristic.uuid == FLOW_UUID:
            characteristic.value = [self.active_flow]
        return characteristic.value

    def write_request(self, characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        if characteristic.uuid == FLOW_UUID:
            self.logger.debug("Request set-flow")
            self.change_state(characteristic, value)
            
        elif characteristic.uuid == SESSION_LIST_REQ_UUID:
            self.logger.debug("Request session list")
            task = asyncio.create_task(self.session_list())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        elif characteristic.uuid == DETECTIONS_LIST_REQ_UUID:
            session = DetectionsForSessionMessage.from_proto(value).session
            self.logger.debug(f"Request detections list {session}")
            task = asyncio.create_task(self.detections_list(session))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        elif characteristic.uuid == IMAGE_REQ_UUID:
            req = DetectionReferenceMessage.from_proto(value)
            self.logger.debug(f"Request image {req.session, req.detection}")
            task = asyncio.create_task(self.segmented_image(req.session, req.detection))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)


    def change_state(self, characteristic, value):
        old_state = self.active_flow
        new_state = int(value[0])
        self.logger.debug(f"Change state - old = {old_state} new = {new_state}")

        if old_state is NO_FLOW:
            if new_state == DETECT_FLOW:
                self.process = Process(target=self.detector, args=())
                self.process.start()
            elif new_state == PREVIEW_FLOW:
                self.process = Process(target=self.previewer, args=())
                self.process.start()

        elif old_state != DETECT_FLOW:
            if new_state == NO_FLOW:
                self.process.terminate()
            elif new_state == PREVIEW_FLOW:
                self.process.terminate()
                self.process = Process(target=self.previewer, args=())
                self.process.start()

        elif old_state != PREVIEW_FLOW:
            if new_state == NO_FLOW:
                self.process.terminate()
            elif new_state == DETECT_FLOW:
                self.process.terminate()
                self.process = Process(target=self.detector, args=())
                self.process.start()

        characteristic.value = [new_state]
        self.active_flow = new_state
        #characteristic.update()

        self.logger.debug(f"flow set to {new_state}")

    async def session_list(self):
        self.logger.debug("Session list")
        sessions = self.session_server.list_sessions()
        for session in sessions:
            self.logger.debug(f"Updating Session = {session}")
            await self.session_notifier.notify_session_details(session[0], session[1])

    async def detections_list(self, session):
        self.logger.debug("Detections list")
        detections = self.session_server.list_detections_for_session(session)
        for detection in detections:
            self.logger.debug(f"Notifying detection = {detection}")
            await self.detection_notifier.notify_detection_meta(detections[detection])

    async def segmented_image(self, session, detection):
        """
        Segment a detection image and sent the parts via the 'image_sender'
        """
        meta, img = self.session_server.get_image_data(session, detection)
        segments = math.ceil(len(img) / IMAGE_SEGMENT)

        #Send the header
        await self.image_sender.send_header(session, detection, meta.width, meta.height, segments)

        start_index = 0
        segment = 1
        while start_index < len(img):
            img_seg = img[start_index:start_index + IMAGE_SEGMENT]
            await self.image_sender.send_segment(session, detection, segment, img_seg)
            segment = segment + 1
            start_index = start_index + IMAGE_SEGMENT

        if start_index != len(img):
            segment = segment + 1
            img_seg = img[start_index:]
            await self.image_sender.send_segment(session, segment, segment, img_seg)

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


