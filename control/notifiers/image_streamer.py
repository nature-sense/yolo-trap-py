import asyncio
import copy
import logging
import math

from thonny.plugins.microbit.api_stubs.time import sleep

from control.bluetooth_messages import FrameHeaderMessage, FrameSegmentMessage
from control.notifiers.notifier import Notifier
from control.uuids import SERVICE_UUID, PREVIEW_STREAM_UUID

IMAGE_SEGMENT = 400

class FrameBuffer :
    def __init__(self):
        self.frame = None
        self.event = asyncio.Event()
        self.lock = asyncio.Lock()

    async def write_frame(self, timestamp, frame):
        async with self.lock:
            self.frame = FrameDesc(timestamp, frame)
            self.event.set()

    async def read_frame(self):
        await self.event.wait()
        async with self.lock:
            self.event.clear() # stops re-reading the same frame
            return copy.deepcopy(self.frame)

class FrameDesc :
    def __init__(self,timestamp, frame):
        self.timestamp = timestamp
        self.frame = frame



class ImageStreamer(Notifier) :
    def __init__(self, bluetooth_server):
        super().__init__(bluetooth_server,  SERVICE_UUID, PREVIEW_STREAM_UUID)
        self.frame_buffer = FrameBuffer()
        self.logger = logging.getLogger()
        self.latest_frame = None

    async  def addFrame(self, timestamp, frame):
       await self.frame_buffer.write_frame(timestamp, frame)

    async def publish(self):
        characteristic = self.bluetooth_server.get_characteristic(self.characteristic)

        while True:
            frame_desc = await self.frame_buffer.read_frame()
            if frame_desc is not None :
                frame = frame_desc.frame
                timestamp = frame_desc.timestamp
                print(f"got frame {timestamp}")
                segments = math.ceil(len(frame) / IMAGE_SEGMENT)

                # Send the header
                msg = FrameHeaderMessage(timestamp, 0, 0,segments).to_proto()
                characteristic.value = msg
                result = self.bluetooth_server.update_value(self.service, self.characteristic)
                if result is False:
                    self.logger.error(f"Send notification failed {result}")

                start_index = 0
                segment = 1
                while start_index < len(frame):
                    img_seg = frame[start_index:start_index + IMAGE_SEGMENT]
                    msg = FrameSegmentMessage(timestamp, segment, img_seg).to_proto()
                    characteristic.value = msg
                    result = self.bluetooth_server.update_value(self.service, self.characteristic)
                    if result is False :
                        self.logger.error(f"Send notification failed {result}")
                    segment = segment + 1
                    start_index = start_index + IMAGE_SEGMENT

                if start_index != len(frame):
                    segment = segment + 1
                    img_seg = frame[start_index:]
                    msg = FrameSegmentMessage(timestamp, segment, img_seg).to_proto()
                    characteristic.value = msg
                    result = self.bluetooth_server.update_value(self.service, self.characteristic)
                    if result is False :
                        self.logger.error(f"Send notification failed {result}")
                self.logger.debug(f"last segment = {segment}")

            else:
                await asyncio.sleep(1)



