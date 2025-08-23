from mqtt import mqtt_pb2


class SessionMessage :
    def __init__(self, session):
        self.session = session

    @staticmethod
    def from_proto(proto):
        msg = mqtt_pb2.SessionMsg()
        msg.ParseFromString(proto)
        return SessionMessage(msg.session)

    def to_proto(self):
        session_msg = mqtt_pb2.SessionMsg()
        session_msg.session = self.session
        return session_msg.SerializeToString()


class SessionDetailsMessage :
    def __init__(self, session, detections):
        self.session = session
        self.detections = detections

    @staticmethod
    def from_proto(proto):
        msg = mqtt_pb2.SessionDetailsMsg()
        msg.ParseFromString(proto)
        return SessionDetailsMessage(msg.session, msg.detections)

    def to_proto(self):
        session_msg = mqtt_pb2.SessionDetailsMsg()
        session_msg.session = self.session
        session_msg.detections = self.detections
        return session_msg.SerializeToString()


class DetectionMessage :
    def __init__(self, session, detection, created, updated, score, clazz, width, height, data ):
        self.session = session
        self.detection = detection
        self.created = created
        self.updated = updated
        self.score = score
        self.clazz = clazz
        self.width = width
        self.height = height
        self.data = data

    @staticmethod
    def from_detection_metadata(meta):
        return DetectionMessage(
            meta.session,
            meta.detection,
            meta.created,
            meta.updated,
            meta.score,
            meta.clazz,
            meta.width,
            meta.height,
            meta.data
        )

    @staticmethod
    def from_proto(proto):
        msg = mqtt_pb2.DetectionMsg()
        msg.ParseFromString(proto)
        return DetectionMessage(
            msg.session,
            msg.detection,
            msg.created,
            msg.updated,
            msg.score,
            msg.clazz,
            msg.width,
            msg.height,
            msg.data
        )

    def to_proto(self):
        msg = mqtt_pb2.DetectionMsg()
        msg.session = self.session
        msg.detection = self.detection
        msg.created = self.created
        msg.updated = self.updated
        msg.score = self.score
        msg.clazz = self.clazz
        msg.width = self.width
        msg.height = self.height
        msg.data = self.data
        return msg.SerializeToString()


class StateMessage :
    def __init__(self, active_flow):
        self.active_flow = active_flow

    @staticmethod
    def from_proto(proto):
        msg = mqtt_pb2.StateMsg()
        msg.ParseFromString(proto)
        return StateMessage(msg.active_flow)

    def to_proto(self):
        msg = mqtt_pb2.StateMsg()
        msg.active_flow = self.active_flow
        return msg.SerializeToString()


class SettingsMessage :
    def __init__(self, trap_name, wifi_ssid, wifi_password,wifi_enabled, max_sessions, min_score):
        self.trap_name = trap_name
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.wifi_enabled = wifi_enabled
        self.max_sessions = max_sessions
        self.min_score = min_score

    @staticmethod
    def from_settings(settings):
        return SettingsMessage(
            settings.trap_name,
            settings.wifi_ssid,
            settings.wifi_password,
            settings.wifi_enabled,
            settings.max_sessions,
            settings.min_score
        )

    @staticmethod
    def from_proto(proto):
        msg = mqtt_pb2.SettingsMsg()
        msg.ParseFromString(proto)
        return SettingsMessage(
            msg.trap_name,
            msg.wifi_ssid,
            msg.wifi_password,
            msg.wifi_enabled,
            msg.max_sessions,
            msg.min_score
        )

    def to_proto(self):
        msg = mqtt_pb2.SettingsMsg()
        msg.trap_name = self.trap_name
        msg.wifi_ssid = self.wifi_ssid
        msg.wifi_password = self.wifi_password
        msg.wifi_enabled = self.wifi_enabled
        msg.max_sessions = self.max_sessions
        msg.min_score = self.min_score