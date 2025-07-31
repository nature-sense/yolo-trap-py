from ipc.session_messages import NewSessionMessage, NewDetectionMessage, UpdateDetectionMetaMessage, \
    UpdateDetectionMessage


class FixedSizeMap:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.keys = []

    def clear(self):
        self.map.clear()
        self.keys.clear()

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

class DetectionsCache:
    def __init__(self, size, ipc_client):
        self.cache = FixedSizeMap(size)
        self.ipc = ipc_client

    async def new_session(self, session):
        self.cache.clear()
        msg = NewSessionMessage(session).to_proto()
        await self.ipc.send(msg)

    def get_detection_metadata(self, detection):
        return self.cache.get(detection)

    async def new_detection(self, detection_metadata, image):
        self.cache.add(detection_metadata.detection, detection_metadata)
        msg = NewDetectionMessage.from_detection_metadata(detection_metadata, image).to_proto()
        await self.ipc.send(msg)

    async def update_detection_meta(self, detection_metadata):
        self.cache.update(detection_metadata.detection, detection_metadata)
        msg = UpdateDetectionMetaMessage.from_detection_metadata(detection_metadata).to_proto()
        await self.ipc.send(msg)

    async def update_detection(self, detection_metadata, image):
        self.cache.update(detection_metadata.detection, detection_metadata)
        msg = UpdateDetectionMessage.from_detection_metadata(detection_metadata, image).to_proto()
        await self.ipc.send(msg)



