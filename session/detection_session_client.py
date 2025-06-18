from session.ipc import IpcClient
from session.session_messages import NewSessionMessage, NewDetectionMessage, UpdateDetectionMessage, UpdateDetectionMetaMessage


class FixedSizeMap:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.keys = []

    def add(self, key, entry):
        if len(self.map) >= self.capacity:
            oldest_key = self.keys.pop(0)
            del self.map[oldest_key]
        self.map[key] = entry
        self.keys.append(key)

    def update(self, key, entry):
        self.map[key] = entry
        self.keys.remove(key)
        self.keys.append(key)

    def get(self, key):
        val = self.map.get(key)
        return val

    def remove(self, key):
        if key in self.map:
            del self.map[key]
            self.keys.remove(key)

    def __len__(self):
        return len(self.map)

class DetectionSessionClient:
    def __init__(self, size, session):
        self.session = session
        self.cache = FixedSizeMap(size)
        self.ipc = IpcClient()

        # Send the NEW_SESSION message
        msg = NewSessionMessage(self.session).to_proto()
        self.ipc.send(msg)

    def get_detection_metadata(self, detection):
        return self.cache.get(detection)

    def new_detection(self, detection_metadata, image):
        self.cache.add(detection_metadata.detection, detection_metadata)
        msg = NewDetectionMessage.from_detection_metadata(detection_metadata, image).to_proto()
        self.ipc.send(msg)

    def update_detection_meta(self, detection_metadata):
        self.cache.update(detection_metadata.detection, detection_metadata)
        msg = UpdateDetectionMetaMessage.from_detection_metadata(detection_metadata).to_proto()
        self.ipc.send(msg)

    def update_detection(self, detection_metadata, image):
        self.cache.update(detection_metadata.detection, detection_metadata)
        msg = UpdateDetectionMessage.from_detection_metadata(detection_metadata, image).to_proto()
        self.ipc.send(msg)



