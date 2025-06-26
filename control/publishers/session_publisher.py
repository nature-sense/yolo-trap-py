import asyncio
import logging

from control.bluetooth_messages import NewSessionMessage, DeleteSessionMessage, SessionDetailsMessage
from control.publishers.publisher import Publisher
from control.uuids import SESSION_NOTIF_UUID, SERVICE_UUID

class SessionPublisher(Publisher) :
    def __init__(self, bluetooth_server):
        super().__init__(bluetooth_server,  SERVICE_UUID, SESSION_NOTIF_UUID)

    async def notify_new_session(self, session)  :
        msg = NewSessionMessage(session).to_proto()
        await self.notif_queue.put(msg)

    async def notify_delete_session(self, session) :
        msg = DeleteSessionMessage(session).to_proto()
        await self.notif_queue.put(msg)

    async def notify_session_details(self, session, detections):
        msg = SessionDetailsMessage(session, detections).to_proto()
        await self.notif_queue.put(msg)
