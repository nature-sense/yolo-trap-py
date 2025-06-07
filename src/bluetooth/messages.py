from  src.bluetooth import messages_pb2
from src.session.image_metadata import ImageMetadata


class ImageReference :
    def __init__(self, session, image) :
        self.session = session
        self.image = image

    def to_proto(self) :
        msg = messages_pb2.ImageReferenceMsg()
        msg.session = self.session
        msg.image = self.image
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = messages_pb2.ImageReferenceMsg()
        msg.ParseFromString(proto)
        return ImageReference(msg.session, msg.image)

class SessionReference :
    def __init__(self, session : str) :
        self.session = session

    def to_proto(self):
        msg = messages_pb2.SessionReferenceMsg()
        msg.session = self.session
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = messages_pb2.SessionReferenceMsg()
        msg.ParseFromString(proto)
        return SessionReference(msg.session)

class SessionDetails :
    def __init__(self, session : str, images : int) :
        self.session = session
        self.images = images

    def to_proto(self):
        msg = messages_pb2.SessionDetailsMsg()
        msg.session = self.session
        msg.images = self.images
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = messages_pb2.SessionDetailsMsg()
        msg.ParseFromString(proto)
        return SessionDetails(msg.session, msg.images)

class ImageSequenceHeader:
    def __init__(self,  meta_data : ImageMetadata, segments) :
        self.metadata = meta_data
        self.segments = segments

    def to_proto(self):
        msg = messages_pb2.ImageSequenceHeaderMsg()
        msg.session = self.metadata.session
        msg.image = self.metadata.image
        msg.created = self.metadata.created
        msg.updated = self.metadata.updated
        msg.score = self.metadata.score
        msg.clazz = self.metadata.clazz
        msg.width = self.metadata.width
        msg.height = self.metadata.height
        msg.segments = self.segments
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = messages_pb2.ImageSequenceHeaderMsg()
        msg.ParseFromString(proto)
        return ImageSequenceHeader(
            ImageMetadata(
                msg.session,
                msg.image,
                msg.created,
                msg.updated,
                msg.score,
                msg.clazz,
                msg.width,
                msg.height
            ),
            msg.segments
        )


class ImageSequenceSegment :
    def __init__(self, segment, data) :
        self.segment = segment
        self.data = data

    def to_proto(self):
        msg = messages_pb2.ImageSequenceSegmentMsg()
        msg.segment = self.segment
        msg.data = self.data
        return msg.SerializeToString()

    @staticmethod
    def from_proto(proto):
        msg = messages_pb2.ImageSequenceSegmentMsg()
        msg.ParseFromString(proto)
        return ImageSequenceSegment(msg.segment, msg.data)

