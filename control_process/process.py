import asyncio
import logging

from ipc.ipc import IpcServer

from control_process.session_manager import SessionManager
from control_process.bluetooth_controller import BluetoothController
from settings.settings_manager import SettingsManager


def run_control_process() :
    logging.debug("Starting control process")
    cp = ControlProcess()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cp.start_services())

class ControlProcess :

    async def start_services(self):
        settings_manager = SettingsManager()

        session_manager = SessionManager(settings_manager)
        await asyncio.gather(session_manager.ipc_server.receiver_task(), session_manager.bluetooth_controller.bluetooth_task())
