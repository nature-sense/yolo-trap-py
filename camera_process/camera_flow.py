import logging
import picamera2
import asyncio

from abc import ABC, abstractmethod
from picamera2 import CompletedRequest, Picamera2

from ipc.active_flow import ActiveFlow
from ipc.session_messages import ActiveFlowMessage


class CameraFlow(ABC):

    name = ""

    def __init__(self, ipc_client):
        self.picam2 = None
        self.loop = asyncio.get_running_loop()
        self.ipc_client = ipc_client
        self.logger = logging.getLogger()
        self.exit = False

    def stop(self):
        self.exit = True

    @abstractmethod
    async def init_camera(self):
        pass

    @abstractmethod
    async def start_flow(self):
        pass


    async def get_image(self) -> CompletedRequest:
        logging.debug("Get image")
        future = self.loop.create_future()
        def job_done_callback(job: "picamera2.job.Job"):
            try:
                result = job.get_result()
            except Exception as e:
                self.loop.call_soon_threadsafe(future.set_exception, e)
            else:
                self.loop.call_soon_threadsafe(future.set_result, result)
        self.picam2.capture_request(signal_function=job_done_callback)
        return await future


    @abstractmethod
    async def process_result(self, result):
        pass

    @abstractmethod
    async def close_camera(self):
        pass

    async def do_flow(self) :
        try :
            await self.init_camera()
            await self.start_flow()

            while not self.exit :
                result = await self.get_image()
                await self.process_result(result)

            self.exit = False
            await self.close_camera()
            msg = ActiveFlowMessage(ActiveFlow.NO_FLOW).to_proto()
            await self.ipc_client.send(msg)

        except asyncio.CancelledError as e:
            logging.error(e)

