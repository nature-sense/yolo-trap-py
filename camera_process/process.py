import asyncio
import logging

from camera_process.detect_flow import DetectFlow
from camera_process.preview_flow import PreviewFlow
from ipc.active_flow import ActiveFlow
from ipc.control_messages import ControlMessage, MsgType
from ipc.ipc import IpcClient, MessageHandler


class FlowDescriptor:
    def __init__(self, flow_object, task):
        self.object = flow_object
        self.task = task

class CameraProcess(MessageHandler):
    def __init__(self, settings, camera):
        self.ipc = None
        self.detect_flow = None
        self.preview_flow = None
        self.settings = settings
        self.camera = camera
    async def start_services(self):
        logging.debug("Starting camera services")
        self.ipc = IpcClient(self)
        self.detect_flow = FlowDescriptor(DetectFlow(self.ipc, self.camera), None)
        self.preview_flow = FlowDescriptor(PreviewFlow(self.ipc, self.camera), None)
        await asyncio.gather(self.ipc.receiver_task())

    def handle_message(self, proto):
        type, msg = ControlMessage.from_proto(proto)

        if type == MsgType.SET_ACTIVE_FLOW :
            flow = ActiveFlow(msg.flow)
            logging.debug(f"Received SET_ACTIVE_FLOW {msg.flow}")

            if flow == ActiveFlow.NO_FLOW :
                if self.detect_flow.task is not None :
                    self.detect_flow.object.stop()
                    self.detect_flow.task = None
                if self.preview_flow.task is not None :
                    self.preview_flow.object.stop()
                    self.preview_flow.task = None

            elif flow == ActiveFlow.DETECT_FLOW :
                if self.detect_flow.task is None :
                    self.detect_flow.task = asyncio.create_task(self.detect_flow.object.do_flow())

            elif flow == ActiveFlow.PREVIEW_FLOW :
                if self.preview_flow.task is None :
                    self.preview_flow.task = asyncio.create_task(self.preview_flow.object.do_flow())

        else:
            pass


