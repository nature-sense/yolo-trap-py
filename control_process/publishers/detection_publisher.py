from control_process.bluetooth_messages import DetectionMetadataMessage
from control_process.publishers.publisher import Publisher
from control_process.uuids import DETECTION_NOTIF_UUID, SERVICE_UUID

class DetectionPublisher(Publisher) :
    def __init__(self, bluetooth_server,):
        super().__init__(bluetooth_server,  SERVICE_UUID, DETECTION_NOTIF_UUID)

    async def notify_detection_meta(self, detection_meta):
        msg = DetectionMetadataMessage.from_metadata(detection_meta).to_proto()
        await self.notif_queue.put(msg)
