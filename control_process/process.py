import asyncio
import logging

from control_process.session_manager import SessionManager

class ControlProcess :

    def __init__(self, settings):
        self.settings = settings

    async def start_services(self):
        logging.debug("Starting control services")

        session_manager = SessionManager(self.settings)
        await asyncio.gather(
            session_manager.ipc_server.receiver_task(),
            session_manager.protocol_server.server_task(),
            session_manager.bluetooth_task()
        )