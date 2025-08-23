import asyncio
import logging

from aioreactive import AsyncAnonymousObserver
from websockets.asyncio.server import serve
from control_process import trap_protocol_pb2
from ipc.active_flow import ActiveFlow

from settings.settings import Settings

class TrapProtocolServer :
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cache = self.session_manager.sessions_cache
        self.websocket = None
        self.tasks = [];

    async def server_task(self):
        self.tasks = [
            asyncio.create_task(self.new_session_task()),
            asyncio.create_task(self.del_session_task()),
            asyncio.create_task(self.session_details_task()),
            asyncio.create_task(self.new_detection_task()),
            asyncio.create_task(self.active_flow_task())
        ]

        async with serve(self.handler, "", 8002) as server:
            await server.serve_forever()

        #await websocket.send(pmsg.SerializeToString(), text=False)

    async def handler(self, websocket):
        #if self.websocket is not None :
        #    return

        self.websocket = websocket

        logging.debug(f"creating tasks websocket ")
        incom_task = asyncio.create_task(self.incoming_task())

        await incom_task # exits when socket gone
        self.websocket = None

    async def incoming_task(self):
        logging.debug("Incoming task started")

        try:
            while True:
                logging.debug("Waiting for message...")

                proto = await self.websocket.recv(decode = False)

                prot_msg = trap_protocol_pb2.TrapProtocolMsg()
                prot_msg.ParseFromString(proto)

                msg_type = prot_msg.WhichOneof('inner')
                logging.debug(f"Received message {msg_type}")

                # get sessions -
                if msg_type =="getSessionMsg":
                    logging.debug("Received getSessionMsg")
                    for sess in self.session_manager.list_sessions() :
                        await self.send_session_details_msg(sess[0], sess[1])

                elif msg_type == "getDetectionMsg" :
                    logging.debug("Received getDetectionMsg")
                    s = prot_msg.getDetectionMsg.session
                    for det in self.session_manager.sessions_cache.get_detections_for_session(s) :
                        await self.send_detection_msg(det[0], det[1])

                elif msg_type == "getStateMsg" :
                    logging.debug("Received getStateMsg")
                    state = self.session_manager.get_state()
                    await self.send_state_msg(state)

                elif msg_type == "setStateMsg" :
                    logging.debug("Received setStateMsg")
                    a = prot_msg.setStateMsg.active_flow
                    await self.session_manager.set_active_flow(ActiveFlow(a))

                elif msg_type == "getSettingsMsg" :
                    logging.debug("Received getSettingsMsg")
                    settings = self.session_manager.get_settings()
                    await self.send_settings_msg(settings)

                elif msg_type == "setSettingsMsg" :
                    logging.debug("Received setSettingsMsg")
                    self.session_manager.set_settings(self.settings_msg_to_settings(prot_msg.setSettingsMsg))

        except Exception as e:
            logging.warn(f"Error in incoming_task {e}")

    async def new_session_task(self):
        try :
            async def new_session_sink(s) :
                await self.send_new_session_msg(s)
            sink = AsyncAnonymousObserver(new_session_sink)
            await self.cache.new_session_stream.subscribe_async(sink)
        except Exception as e:
            logging.warn(f"Error in new_session_task {e}")

    async def del_session_task(self):
        try :
            async def del_session_sink(s) :
                await self.send_delete_session_msg(s)
            sink = AsyncAnonymousObserver(del_session_sink)
            await self.cache.del_session_stream.subscribe_async(sink)
        except Exception as e:
            logging.warn(f"Error in del_session_task {e}")

    async def session_details_task(self):
        try :
            async def session_details_sink(s) :
                await self.send_session_details_msg(s[0], s[1])
            sink = AsyncAnonymousObserver(session_details_sink)
            await self.cache.session_details_stream.subscribe_async(sink)
        except Exception as e:
            logging.warn(f"Error in session_details_task {e}")

    async def new_detection_task(self):
        try :
            async def new_detection_sink(d) :
                await self.send_detection_msg(d[0], d[1])
            sink = AsyncAnonymousObserver(new_detection_sink)
            await self.cache.new_detection_stream.subscribe_async(sink)
        except Exception as e:
            logging.warn(f"Error in new_detection_task {e}")

    async def active_flow_task(self):
        try :
            async def active_flow_sink(s) :
                await self.send_state_msg(s)
            sink = AsyncAnonymousObserver(active_flow_sink)
            await self.session_manager.state_stream.subscribe_async(sink)
        except Exception as e:
            logging.warn(f"Error in active_flow_task {e}")

    @staticmethod
    def settings_msg_to_settings(settings_msg):
        return Settings(
            trap_name=settings_msg.trap_name,
            wifi_ssid=settings_msg.wifi_ssid,
            wifi_password=settings_msg.wifi_password,
            wifi_enabled=settings_msg.wifi_enabled,
            max_sessions=settings_msg.max_sessions,
            min_score=settings_msg.min_score,
        )

    async def send_new_session_msg(self, session) :
        logging.debug(f"Sending NewSessionMsg")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.NewSessionMsg()
            msg.session = session
            pmsg.newSessionMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_session_details_msg(self, session, detections):
        logging.debug("Sending SessionDetailsMsg")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.SessionDetailsMsg()
            msg.session = session
            msg.detections = detections
            pmsg.sessionDetailsMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_delete_session_msg(self, session) :
        logging.debug("Sending DeleteSessionMsg")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.DeleteSessionMsg()
            msg.session = session
            pmsg.deleteSessionMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_detection_msg(self, detection, image) :
        logging.debug("Sending DetectionMsg")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.DetectionMsg()
            msg.session = detection.session
            msg.detection = detection.detection
            msg.created = detection.created
            msg.updated = detection.updated
            msg.score = detection.score
            msg.clazz = detection.clazz
            msg.width = detection.width
            msg.height = detection.height
            if image is not None :
                msg.image = image
            pmsg.detectionMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_state_msg(self, state):
        logging.debug(f"Sending StateMsg {state}")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.StateMsg()
            msg.active_flow = state.value
            pmsg.stateMsg.CopyFrom(msg)
            logging.debug(f"Sending msg...")
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_settings_msg(self, settings):
        logging.debug("Sending SettingsMsg")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.SettingsMsg()
            msg.trap_name = settings.trap_name
            msg.wifi_ssid = settings.wifi_ssid
            msg.wifi_password = settings.wifi_password
            msg.wifi_enabled = settings.wifi_enabled
            msg.max_sessions = settings.max_sessions
            msg.min_score = settings.min_score
            pmsg.settingsMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else :
            logging.error("NO WEBSOCKET")

    async def send_image_msg(self, session, detection, image):
        logging.debug("Sending ImageMessage")
        if self.websocket is not None :
            pmsg = trap_protocol_pb2.TrapProtocolMsg()
            msg = trap_protocol_pb2.ImageMsg()
            msg.session = session
            msg.detection = detection
            msg.image = image
            pmsg.settingsMsg.CopyFrom(msg)
            await self.websocket.send(pmsg.SerializeToString(), text=False)
        else:
            logging.error("NO WEBSOCKET")








