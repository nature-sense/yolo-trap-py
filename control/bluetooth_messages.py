from enum import Enum

from control import bluetooth_pb2
from session.detection_metadata import DetectionMetadata

class ImageMsgType(Enum) :
    IMAGE_HEADER = 1,
    IMAGE_SEGMENT = 2,
    UNKNOWN = 3

class SessionMsgType(Enum) :
    NEW_SESSION = 1,
    SESSION_DELETED = 2,
    SESSION_DETAILS = 3,
    UNKNOWN = 4

class FrameMsgType(Enum) :
    FRAME_HEADER = 1
    FRAME_SEGMENT = 2
    UNKNOWN = 3


# ========================================================================
#                    Session Messages
# ========================================================================
class SessionMessage :
    def from_proto(proto):
        msg = bluetooth_pb2.SessionMsg()
        msg.ParseFromString(proto)
        type = msg.WhichOneof("inner")

        if type == "new_session":
            return SessionMsgType.NEW_SESSION, NewSessionMessage.from_proto(msg.session)
        elif type == "del_session":
            return SessionMsgType.SESSION_DELETED, DeleteSessionMessage.from_proto(msg.ession)
        elif type == 'sess_details':
            return SessionMsgType.SESSION_DETAILS, SessionDetailsMessage.from_proto(msg.ession)
        else:
            return SessionMsgType.UNKNOWN, None


class NewSessionMessage :
    def __init__(self, session : str) :
        self.session = session

    def to_proto(self):
        session_msg = bluetooth_pb2.SessionMsg()
        new_session_msg = bluetooth_pb2.NewSessionMsg()
        new_session_msg.session = self.session
        session_msg.new_session.CopyFrom(new_session_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return NewSessionMessage(msg.session)


class DeleteSessionMessage :
    def __init__(self, session : str) :
        self.session = session

    def to_proto(self):
        session_msg = bluetooth_pb2.SessionMsg()
        del_session_msg = bluetooth_pb2.SessionDeletedMsg()
        del_session_msg.session = self.session
        session_msg.del_session.CopyFrom(del_session_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return DeleteSessionMessage(msg.session)

class SessionDetailsMessage :
    def __init__(self, session : str, detections : int) :
        self.session = session
        self.detections = detections

    def to_proto(self):
        session_msg = bluetooth_pb2.SessionMsg()
        details_msg = bluetooth_pb2.SessionDetailsMsg()
        details_msg.session = self.session
        details_msg.detections = self.detections
        session_msg.sess_details.CopyFrom(details_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return SessionDetailsMessage(msg.session, msg.images)

# ========================================================================
#                    Image Messages -> send only
# ========================================================================
class ImageHeaderMessage :
    def __init__(self, session, detection, width, height, segments):

        self.session = session
        self.detection  =  detection
        self.width = width
        self.height = height
        self.segments = segments

    def to_proto(self):
        img_msg = bluetooth_pb2.ImageMsg()
        header_msg = bluetooth_pb2.ImageHeaderMsg()
        header_msg.session = self.session
        header_msg.detection = self.detection
        header_msg.width = self.width
        header_msg.height = self.height
        header_msg.segments = self.segments
        img_msg.header.CopyFrom(header_msg)
        return img_msg.SerializeToString()

class ImageSegmentMessage:
    def __init__(self, session, detection, segment, data):
        self.session = session
        self.detection = detection
        self.segment = segment
        self.data = data

    def to_proto(self):
        img_msg = bluetooth_pb2.ImageMsg()
        segment_msg = bluetooth_pb2.ImageSegmentMsg()
        segment_msg.session = self.session
        segment_msg.detection = self.detection
        segment_msg.segment = self.segment
        segment_msg.data = self.data
        img_msg.segment.CopyFrom(segment_msg)
        return img_msg.SerializeToString()

# ========================================================================
#                    Detection Messages
# ========================================================================
class DetectionsForSessionMessage:
    def __init__(self, session) :
        self.session = session

    @staticmethod
    def from_proto(proto):
        msg = bluetooth_pb2.DetectionsForSessionMsg()
        msg.ParseFromString(proto)
        return DetectionsForSessionMessage(msg.session,)

class DetectionReferenceMessage :
    def __init__(self, session, detection) :
        self.session = session
        self.detection = detection

    def to_proto(self) :
        msg = bluetooth_pb2.DetectionReferenceMsg()
        msg.session = self.session
        msg.detection = self.detection
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = bluetooth_pb2.DetectionReferenceMsg()
        msg.ParseFromString(proto)
        return DetectionReferenceMessage(msg.session, msg.detection)

class DetectionMetadataMessage:
    def __init__(self,  session, detection, created, updated, score, clazz, width, height) :
        self.session = session
        self.detection = detection
        self.created = created
        self.updated = updated
        self.score = score
        self.clazz = clazz
        self.width = width
        self.height = height

    @staticmethod
    def from_metadata(metadata):
        return DetectionMetadataMessage(
            metadata.session,
            metadata.detection,
            metadata.created,
            metadata.updated,
            metadata.score,
            metadata.clazz,
            metadata.width,
            metadata.height
        )

    def to_proto(self):
        msg = bluetooth_pb2.DetectionMetadataMsg()
        msg.session = self.session
        msg.detection = self.detection
        msg.created = self.created
        msg.updated = self.updated
        msg.score = self.score
        msg.clazz = self.clazz
        msg.width = self.width
        msg.height = self.height

        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = bluetooth_pb2.DetectionMetadataMsg()
        msg.ParseFromString(proto)
        return DetectionMetadata(
            msg.session,
            msg.detection,
            msg.created,
            msg.updated,
            msg.score,
            msg.clazz,
            msg.width,
            msg.height
        )

# ========================================================================
#                        Frame Messages - send only
# ========================================================================
class FrameHeaderMessage :
    def __init__(self, timestamp, width, height, segments):
        self.timestamp = timestamp
        self.width = width
        self.height = height
        self.segments = segments

    def to_proto(self):
        img_msg = bluetooth_pb2.FrameMsg()
        header_msg = bluetooth_pb2.FrameHeaderMsg()
        header_msg.timestamp = self.timestamp
        header_msg.width = self.width
        header_msg.height = self.height
        header_msg.segments = self.segments
        img_msg.header.CopyFrom(header_msg)
        return img_msg.SerializeToString()


class FrameSegmentMessage:
    def __init__(self, timestamp, segment, data):
        self.timestamp = timestamp
        self.segment = segment
        self.data = data

    def to_proto(self):
        img_msg = bluetooth_pb2.FrameMsg()
        segment_msg = bluetooth_pb2.FrameSegmentMsg()
        segment_msg.timestamp = self.timestamp
        segment_msg.segment = self.segment
        segment_msg.data = self.data
        img_msg.segment.CopyFrom(segment_msg)
        return img_msg.SerializeToString()

