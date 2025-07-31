from ipc import ipc_pb2
from enum import Enum

class MsgType(Enum) :
    SET_ACTIVE_FLOW = 1,
    UNKNOWN = 2


class SetActiveFlowMessage:
    def __init__(self, flow):
        self.flow = flow

    def to_proto(self):
        control_msg = ipc_pb2.ControlMsg()
        flow_msg = ipc_pb2.SetActiveFlowMsg()
        flow_msg.flow = self.flow.value
        control_msg.set_flow.CopyFrom(flow_msg)
        return control_msg.SerializeToString()

    @staticmethod
    def from_proto(msg):
        return SetActiveFlowMessage(msg.flow)


class ControlMessage :

    @staticmethod
    def from_proto(proto):
        try:
            msg = ipc_pb2.ControlMsg()
            msg.ParseFromString(proto)
            type = msg.WhichOneof("inner")

            print(f"Message type = {type}")

            if type == "set_flow":
                return MsgType.SET_ACTIVE_FLOW, SetActiveFlowMessage.from_proto(msg.set_flow)
            else :
                return MsgType.UNKNOWN, None
        except Exception as e:
            return MsgType.UNKNOWN, None
