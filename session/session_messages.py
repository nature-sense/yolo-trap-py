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
    UNKNOWN = 5

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
    def __init__(self, updated):
        self.updated = updated

    @staticmethod
    def from_detection_metadata(detection_metadata):
        return UpdateDetectionMetaMessage(detection_metadata.updated)

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        upd_detect_meta_msg = session_pb2.UpdateDetectionMetaMsg()
        upd_detect_meta_msg.updated = self.updated
        session_msg.update_detection_meta.CopyFrom(upd_detect_meta_msg)
        return session_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return UpdateDetectionMetaMessage(msg.updated)


class UpdateDetectionMessage :
    def __init__(self, updated, score, width, height, img_data):
        self.updated = updated
        self.score = score
        self.width = width
        self.height = height
        self.img_data = img_data

    @staticmethod
    def from_detection_metadata(detection_metadata, img_data):
        return UpdateDetectionMessage(
            detection_metadata.updated,
            detection_metadata.score,
            detection_metadata.width,
            detection_metadata.height,
            img_data
        )

    def to_proto(self):
        session_msg = session_pb2.SessionMsg()
        upd_detect_msg = session_pb2.UpdateDetectionMsg()
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
            msg.updated,
            msg.score,
            msg.width,
            msg.height,
            msg.img_data
        )

class SessionMessage :
    @staticmethod
    def from_proto(proto):
        try:
            msg = session_pb2.SessionMsg()
            msg.ParseFromString(proto)
            type = msg.WhichOneof("inner")

            if type == "new_session":
                return MsgType.NEW_SESSION, NewSessionMessage.from_proto(msg.new_session)
            elif type == "new_detection":
                return MsgType.NEW_DETECTION, NewDetectionMessage.from_proto(msg.new_detection)
            elif type == "update_detection_meta":
                return MsgType.UPDATE_DETECTION_META, UpdateDetectionMetaMessage.from_proto(msg.update_detection_meta)
            elif type == "update_detection":
                return MsgType.UPDATE_DETECTION, UpdateDetectionMessage.from_proto(msg.update_detection)
            else :
                return MsgType.UNKNOWN, None
        except Exception :
            return MsgType.UNKNOWN, None



