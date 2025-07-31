import logging

import asyncio

from control_process.bluetooth_messages import StateMessage
from control_process.uuids import STATE_NOTIF_UUID, SERVICE_UUID
from camera_process.detect_flow import DetectFlow
from camera_process.preview_flow import PreviewFlow

from ipc.active_flow import ActiveFlow
from ipc.control_messages import SetActiveFlowMessage


class StateController:
    def __init__(self, ipc_server, bluetooth_server) :
        self.logger = logging.getLogger()

        self.detect_flow = DetectFlow.name
        self.preview_flow = PreviewFlow.name

        self.bluetooth_server = bluetooth_server
        self.ipc_server = ipc_server
        self.state_char = self.bluetooth_server.get_characteristic(STATE_NOTIF_UUID)

        self.storage_mounted = False
        self.current_flow = ActiveFlow.NO_FLOW
        self.connected = False
        self.process = None

    def set_active_flow(self, active_flow):
        logging.debug(f"Set active flow = {active_flow}")
        self.current_flow = active_flow
        msg = StateMessage(self.current_flow, self.storage_mounted)
        self.state_char.value = msg.to_proto()
        self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def get_state(self):
        logging.debug(f"Get state")
        msg = StateMessage(self.current_flow, self.storage_mounted)
        self.state_char.value = msg.to_proto()
        self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def set_flow(self, flow):
        loop = asyncio.get_event_loop()

        if self.current_flow is ActiveFlow.NO_FLOW:
            if flow == ActiveFlow.DETECT_FLOW and self.storage_mounted is True:
                msg = SetActiveFlowMessage(flow)
                asyncio.create_task(self.do_set_flow(msg))

            elif flow == ActiveFlow.PREVIEW_FLOW:
                msg = SetActiveFlowMessage(flow)
                asyncio.create_task(self.do_set_flow(msg))

        else :
            msg = SetActiveFlowMessage(flow)
            asyncio.create_task(self.do_set_flow(msg))

    async def do_set_flow(self, msg):
        await self.ipc_server.send(msg.to_proto())

    def set_storage_state(self, state):
        logging.debug(f"Setting storage state = {state}")
        self.storage_mounted = state
        if state is False and self.current_flow is ActiveFlow.DETECT_FLOW :
            self.process.terminate()
            self.current_flow = ActiveFlow.NO_FLOW

        msg = StateMessage(self.current_flow, self.storage_mounted)
        self.state_char.value = msg.to_proto()
        result = self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def connection(self, state):
        self.connected = state
        #if self.current_flow is PREVIEW_FLOW:
        #    return NO_FLOW






