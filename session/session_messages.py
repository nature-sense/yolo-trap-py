#!/usr/bin/env python
"""
Python wrappers for the Session Protocol-buffer messages.
"""
__author__ = "Steve"
__contact__ = "steve@naturesense.io"
__copyright__ = "Copyright 2025, NatureSense"

from session import session_pb2
from enum import Enum


class MsgType(Enum) :
    NEW_SESSION = 1,
    NEW_DETECTION = 2,
    UPDATE_DETECTION_META = 3,
    UPDATE_DETECTION = 4,
    STREAM_FRAME = 5,
    STORAGE = 6.
    UNKNOWN = 7

class NewSessionMessage :

    def __init__(self, session):
        self.session = session

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        new_msg = session_pb2.NewSessionMsg()
        new_msg.session = self.session
        session_msg.new_session.CopyFrom(new_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        #msg = session_pb2.NewSessionMsg()
        #msg.ParseFromString(proto)
        return NewSessionMessage(msg.session)


class NewDetectionMessage :
    def __init__(self, detection, created, score, clazz, width, height, img_data):
        self.detection = detection
        self.created = created
        self.score = score
        self.clazz = clazz
        self.width = width
        self.height = height
        self.img_data = img_data

    @staticmethod
    def from_detection_metadata(detection_metadata, img_data):
        return NewDetectionMessage(
            detection_metadata.detection,
            detection_metadata.created,
            detection_metadata.score,
            detection_metadata.clazz,
            detection_metadata.width,
            detection_metadata.height,
            img_data
        )

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        new_detect_msg = session_pb2.NewDetectionMsg()
        new_detect_msg.detection = self.detection
        new_detect_msg.created = self.created
        new_detect_msg.score = self.score
        new_detect_msg.clazz = self.clazz
        new_detect_msg.width = self.width
        new_detect_msg.height = self.height
        new_detect_msg.img_data = self.img_data
        session_msg.new_detection.CopyFrom(new_detect_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return NewDetectionMessage(
            msg.detection,
            msg.created,
            msg.score,
            msg.clazz,
            msg.width,
            msg.height,
            msg.img_data
        )

class UpdateDetectionMetaMessage :
    def __init__(self, detection, updated):
        self.detection = detection
        self.updated = updated

    @staticmethod
    def from_detection_metadata(detection_metadata):
        return UpdateDetectionMetaMessage(detection_metadata.detection, detection_metadata.updated)

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        upd_detect_meta_msg = session_pb2.UpdateDetectionMetaMsg()
        upd_detect_meta_msg.detection = self.detection
        upd_detect_meta_msg.updated = self.updated
        session_msg.update_detection_meta.CopyFrom(upd_detect_meta_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return UpdateDetectionMetaMessage(msg.detection, msg.updated)


class UpdateDetectionMessage :
    def __init__(self, detection, updated, score, width, height, img_data):
        self.detection = detection
        self.updated = updated
        self.score = score
        self.width = width
        self.height = height
        self.img_data = img_data

    @staticmethod
    def from_detection_metadata(detection_metadata, img_data):
        return UpdateDetectionMessage(
            detection_metadata.detection,
            detection_metadata.updated,
            detection_metadata.score,
            detection_metadata.width,
            detection_metadata.height,
            img_data
        )

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        upd_detect_msg = session_pb2.UpdateDetectionMsg()
        upd_detect_msg.detection = self.detection
        upd_detect_msg.updated = self.updated
        upd_detect_msg.score = self.score
        upd_detect_msg.width = self.width
        upd_detect_msg.height = self.height
        upd_detect_msg.img_data = self.img_data
        session_msg.update_detection.CopyFrom(upd_detect_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return UpdateDetectionMessage(
            msg.detection,
            msg.updated,
            msg.score,
            msg.width,
            msg.height,
            msg.img_data
        )

class FrameMessage :
    def __init__(self, timestamp, frame):
        self.timestamp = timestamp
        self.frame = frame

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        prev_frm_msg = session_pb2.FrameMsg()
        prev_frm_msg.timestamp = self.timestamp
        prev_frm_msg.frame = self.frame
        session_msg.stream_frame.CopyFrom(prev_frm_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return FrameMessage(
            msg.timestamp,
            msg.frame,
        )

class StorageMessage:
    def __init__(self, mounted):
        self.mounted = mounted

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        storage_msg = session_pb2.StorageMsg()
        storage_msg.mounted = self.mounted
        session_msg.storage.CopyFrom(storage_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return StorageMessage(
            msg.mounted
        )


class SessionMessage :

    @staticmethod
    def from_proto(proto):
        try:
            msg = session_pb2.SessionMsg()
            msg.ParseFromString(proto)
            type = msg.WhichOneof("inner")

            print(f"Message type = {type}")

            if type == "new_session":
                return MsgType.NEW_SESSION, NewSessionMessage.from_proto(msg.new_session)
            elif type == "new_detection":
                return MsgType.NEW_DETECTION, NewDetectionMessage.from_proto(msg.new_detection)
            elif type == "update_detection_meta":
                return MsgType.UPDATE_DETECTION_META, UpdateDetectionMetaMessage.from_proto(msg.update_detection_meta)
            elif type == "update_detection":
                return MsgType.UPDATE_DETECTION, UpdateDetectionMessage.from_proto(msg.update_detection)
            elif type == "stream_frame":
                return MsgType.STREAM_FRAME, FrameMessage.from_proto(msg.stream_frame)
            elif type == "storage":
                return MsgType.STORAGE, StorageMessage.from_proto(msg.storage)
            else :
                return MsgType.UNKNOWN, None
        except Exception :
            return MsgType.UNKNOWN, None



