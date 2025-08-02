import asyncio

from control_process.session_manager import SessionManager
from settings.settings_manager import SettingsManager

class ControlProcess :

    async def start_services(self):
        settings_manager = SettingsManager()

        session_manager = SessionManager(settings_manager)
        await asyncio.gather(session_manager.ipc_server.receiver_task(), session_manager.bluetooth_controller.bluetooth_task())
