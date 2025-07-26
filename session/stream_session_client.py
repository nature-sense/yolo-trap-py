import logging

from session.session_ipc import SessionIpcClient
from session.session_messages import FrameMessage


class StreamSessionClient:
    def __init__(self):
        self.ipc = SessionIpcClient()
        self.logger = logging.getLogger()


    def stream_frame(self, timestamp, frame):
        msg = FrameMessage(timestamp,frame).to_proto()
        self.logger.debug("Sending frame to session service")
        self.ipc.send(msg)
