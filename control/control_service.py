import asyncio
import logging
import math
import os
from typing import Any

from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

from control.bluetooth_messages import (
    DetectionReferenceMessage,
    DetectionsForSessionMessage, ActiveFlow
)
from control.state_controller import StateController

from control.publishers.detection_publisher import DetectionPublisher
from control.publishers.image_publisher import ImagePublisher
from control.publishers.stream_publisher import StreamPublisher
from control.publishers.session_publisher import SessionPublisher
from control.uuids import SERVICE_UUID, SESSION_LIST_REQ_UUID, SESSION_NOTIF_UUID, DETECTIONS_LIST_REQ_UUID, \
    DETECTION_NOTIF_UUID, IMAGE_REQ_UUID, IMAGE_SEGMENT_UUID, PREVIEW_STREAM_UUID, \
    STATE_NOTIF_UUID, STATE_REQ_UUID, FLOW_SET_UUID, KEEP_ALIVE_UUID

from session.session_service import SessionService

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"

MAX_TRACKING = 10
MAX_SESSIONS = 5
MIN_SCORE = 0.5

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
        self.storage_state_notifier = None
        self.image_sender = None
        self.image_streamer = None
        self.state_controller = None

        self.node_name = os.uname().nodename.upper()
        self.background_tasks = set()


    async def run(self, loop):
        self.trigger.clear()

        # Instantiate the server
        service_name = self.node_name
        self.bluetooth_server = BlessServer(name=service_name, loop=loop)

        self.bluetooth_server.read_request_func = self.read_request
        self.bluetooth_server.write_request_func = self.write_request

        self.session_notifier = SessionPublisher(self.bluetooth_server)
        self.detection_notifier = DetectionPublisher(self.bluetooth_server)
        self.image_sender = ImagePublisher(self.bluetooth_server)
        self.image_streamer = StreamPublisher(self.bluetooth_server)

        # Add Service
        await self.bluetooth_server.add_new_service(SERVICE_UUID)
        await self.add_notif_char(PREVIEW_STREAM_UUID, bin(0)),

        await self.add_read_write_char(FLOW_SET_UUID, bin(0))
        await self.add_read_write_char(STATE_REQ_UUID, bin(0))
        await self.add_notif_char(STATE_NOTIF_UUID, bin(0))

        await self.add_read_write_char(SESSION_LIST_REQ_UUID, bin(0))
        await self.add_notif_char(SESSION_NOTIF_UUID, bin(0))

        await self.add_read_write_char(DETECTIONS_LIST_REQ_UUID, bin(0))
        await self.add_notif_char(DETECTION_NOTIF_UUID, bin(0))

        await self.add_read_write_char(IMAGE_REQ_UUID, bin(0))
        await self.add_notif_char(IMAGE_SEGMENT_UUID, bin(0))

        await self.add_notif_char(KEEP_ALIVE_UUID, bin(0))

        self.state_controller = StateController(self.detector, self.previewer, self.bluetooth_server)
        self.session_server = SessionService(MAX_SESSIONS, self)

        await self.session_notifier.start()
        await self.detection_notifier.start()
        await self.image_sender.start()
        await self.image_streamer.start()
        await self.session_server.start_service()
        await self.bluetooth_server.start()

        task = asyncio.create_task(self.keep_alive_task())
        self.background_tasks.add(task)

        self.logger.debug("Advertising")
        await self.trigger.wait()

    def read_request(self, characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        self.logger.debug(f"Reading {characteristic.value}")

        #if characteristic.uuid == STATE_REQ_UUID:
        #    characteristic.value = self.state_controller.get_state_proto()
        return characteristic.value

    def write_request(self, characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        if characteristic.uuid == STATE_REQ_UUID:
            self.logger.debug("Request trap-state")
            self.state_controller.get_state()

        elif characteristic.uuid == FLOW_SET_UUID:
            self.logger.debug("Request set-flow")
            self.state_controller.set_flow(ActiveFlow(value[0]))

        elif characteristic.uuid == SESSION_LIST_REQ_UUID:
            self.logger.debug("Request session list")
            task = asyncio.create_task(self.session_list_task())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        elif characteristic.uuid == DETECTIONS_LIST_REQ_UUID:
            session = DetectionsForSessionMessage.from_proto(value).session
            self.logger.debug(f"Request detections list {session}")
            task = asyncio.create_task(self.detections_list_task(session))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        elif characteristic.uuid == IMAGE_REQ_UUID:
            req = DetectionReferenceMessage.from_proto(value)
            self.logger.debug(f"Request image {req.session, req.detection}")
            task = asyncio.create_task(self.segmented_image_task(req.session, req.detection))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)


    async def session_list_task(self):
        self.logger.debug("Session list")
        sessions = self.session_server.list_sessions()
        for session in sessions:
            self.logger.debug(f"Updating Session = {session}")
            await self.session_notifier.notify_session_details(session[0], session[1])

    async def detections_list_task(self, session):
        self.logger.debug("Detections list")
        detections = self.session_server.list_detections_for_session(session)
        for detection in detections:
            self.logger.debug(f"Notifying detection = {detection}")
            await self.detection_notifier.notify_detection_meta(detections[detection])

    async def keep_alive_task(self):
        while True:
            self.logger.debug("KEEP ALIVE")

            result = self.bluetooth_server.update_value(SERVICE_UUID, KEEP_ALIVE_UUID)
            await asyncio.sleep(15)

    async def segmented_image_task(self, session, detection):
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


