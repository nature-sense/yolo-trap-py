import logging
from multiprocessing import Process

from sympy import false

from control.bluetooth_messages import StateMessage, ActiveFlow
from control.uuids import STATE_NOTIF_UUID, SERVICE_UUID


class StateController:
    def __init__(self, detect_flow, preview_flow, bluetooth_server) :
        self.logger = logging.getLogger()

        self.detect_flow = detect_flow
        self.preview_flow = preview_flow

        self.bluetooth_server = bluetooth_server
        self.state_char = self.bluetooth_server.get_characteristic(STATE_NOTIF_UUID)

        self.storage_mounted = false
        self.current_flow = ActiveFlow.NO_FLOW
        self.connected = false
        self.process = None

    def get_state(self):
        msg = StateMessage(self.current_flow, self.storage_mounted)
        self.state_char.value = msg.to_proto()
        result = self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def set_flow(self, flow):

        if self.current_flow is ActiveFlow.NO_FLOW:
            if flow == ActiveFlow.DETECT_FLOW and self.storage_mounted is True:
                self.process = Process(target=self.detect_flow, args=())
                self.process.start()

            elif flow == ActiveFlow.PREVIEW_FLOW:
                self.process = Process(target=self.preview_flow, args=())
                self.process.start()

        elif self.current_flow == ActiveFlow.DETECT_FLOW:
            if flow == ActiveFlow.NO_FLOW:
                self.process.terminate()
            elif flow == ActiveFlow.PREVIEW_FLOW:
                self.process.terminate()
                self.process = Process(target=self.preview_flow, args=())
                self.process.start()

        elif self.current_flow == ActiveFlow.PREVIEW_FLOW:
            if flow == ActiveFlow.NO_FLOW:
                self.process.terminate()
            elif flow == ActiveFlow.DETECT_FLOW and self.storage_mounted is True:
                self.process.terminate()
                self.process = Process(target=self.detect_flow, args=())
                self.process.start()

        if self.current_flow is not flow :
            self.current_flow = flow

            msg = StateMessage(self.current_flow, self.storage_mounted)
            self.state_char.value = msg.to_proto()
            result = self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def set_storage_state(self, state):
        self.logger.debug(f"Setting storage state = {state}")
        self.storage_mounted = state
        if state is false and self.current_flow is ActiveFlow.DETECT_FLOW :
            self.process.terminate()
            self.current_flow = ActiveFlow.NO_FLOW

        msg = StateMessage(self.current_flow, self.storage_mounted)
        self.state_char.value = msg.to_proto()
        result = self.bluetooth_server.update_value(SERVICE_UUID, STATE_NOTIF_UUID)

    def connection(self, state):
        self.connected = state
        #if self.current_flow is PREVIEW_FLOW:
        #    return NO_FLOW






