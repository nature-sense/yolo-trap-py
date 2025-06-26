import asyncio
import logging

from control.bluetooth_messages import ImageHeaderMessage, ImageSegmentMessage
from control.publishers.publisher import Publisher
from control.uuids import IMAGE_SEGMENT_UUID, SERVICE_UUID

class ImagePublisher(Publisher) :
    """
    ImagePublisher

    Buffered publisher for sending image segments via the IMAGE_SEGMENT characteristic.

    """
    def __init__(self, bluetooth_server):
        super().__init__(bluetooth_server,  SERVICE_UUID, IMAGE_SEGMENT_UUID)

    async def send_header(self, session, detection, width, height, segments):
        """
        send_header()

        Create and send a protobuf ImageHeaderMsg
        """
        msg = ImageHeaderMessage(session, detection, width, height, segments).to_proto()
        await self.notif_queue.put(msg)

    async def send_segment(self, session, detection, segment, img):
        """
        send_header()

        Create and send a protobuf ImagSegmentMsg
        """
        msg = ImageSegmentMessage(session, detection,segment, img).to_proto()
        await self.notif_queue.put(msg)


