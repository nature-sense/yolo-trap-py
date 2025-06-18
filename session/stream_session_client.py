import logging

from session.ipc import IpcClient
from session.session_messages import FrameMessage


class StreamSessionClient:
    def __init__(self):
        self.ipc = IpcClient()
        self.logger = logging.getLogger()


    def stream_frame(self, timestamp, frame):
        msg = FrameMessage(timestamp,frame).to_proto()
        self.logger.debug("Sending frame to session service")
        self.ipc.send(msg)



