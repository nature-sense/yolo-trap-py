#!/usr/bin/env python
"""
Session Server

Used by the Bluetooth Control process to manage the image and metadata files.
The server receives messages from the detect-flow process via a TCP socket, creates and
modifies directories and files accordingly, and maintains a metadata cache, which allows
state to be queried and notified ia the Bluetooth interface
"""
__author__ = "Steve"
__contact__ = "steve@naturesense.io"
__copyright__ = "Copyright 2025, NatureSense"

import asyncio
import logging
import os
from datetime import datetime

from aioreactive import AsyncSubject
from bless import BlessServer

from control_process.sessions_cache import SessionsCache
from control_process.trap_protocol_server import TrapProtocolServer

from ipc.active_flow import ActiveFlow
from ipc.control_messages import SetActiveFlowMessage
from ipc.detection_metadata import DetectionMetadata
from ipc.ipc import IpcServer
from ipc.session_messages import SessionMessage, MsgType

SESSIONS_DIRECTORY = "./sessions"

session_format = "%Y%m%d$H%M%S"
def session_to_datetime(session) :
    return datetime.strptime(session,session_format)

SERVICE_UUID  = "213e313b-d0df-4350-8e5d-ae657962bb56"

class SessionManager:
    def __init__(self, settings_manager): #, control_service):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(name=__name__)

        self.node_name = os.uname().nodename.upper()

        self.settings_manager = settings_manager
        self.sessions_cache = SessionsCache(SESSIONS_DIRECTORY, self.settings_manager)

        self.state_stream = AsyncSubject()

        self.ipc_server = IpcServer(self)
        self.protocol_server = TrapProtocolServer(self)

        asyncio.create_task(self.sessions_cache.init()) # run asynchronously

        self.active_flow = ActiveFlow.NO_FLOW

        self.bluetooth_server = None
        self.current_session = None
        self.session_dir = None
        self.image_dir = None
        self.metadata_dir = None

    async def bluetooth_task(self):
        logging.debug("Starting bluetooth task")

        # Instantiate the server
        loop = asyncio.get_running_loop()
        self.bluetooth_server = BlessServer(name=self.node_name, loop=loop)
        await self.bluetooth_server.add_new_service(SERVICE_UUID)
        await self.bluetooth_server.start()
        logging.debug("SBluetooth advertising")
        await asyncio.Future()

    async def handle_requests(self, request):
        """
            handle_requests()

            handle handle requests received over the web-socket connection
            Requests are:
                Subscribe Sessions
                Subscribe Detections
                Subscribe State
                Get Settings
                """
        if request is not None :
            pass
           # if request is SubscribeSessionsRequest :
           #     for session in self.sessions_cache.list_sessions() :
           #         resp = SessionDetailsResponse(session[0], session[1])
           #         await self.websocket_server.send_response(resp)


            #elif request is SubscribeDetectionsRequest :

            #    pass

            #elif request is SubscibeStateRequest :
            #    pass

            #elif request is GetSettingsRequest :
            #    settings = self.settings_manager.get_settings()
            #    resp = SettingsResponse.from_settings(settings).to_proto()
            #    await self.websocket_server.send_response(resp)


    async def handle_message(self, proto):
        """
           handle_message()

           handle session messages received on the IPC socket
           Messages are:
               NEW_SESSION
               NEW_DETECTION
               UPDATE_DETECTION_META
               UPDATE_DETECTION
               PREVIEW_FRAME

        """

        type, msg = SessionMessage.from_proto(proto)
        logging.debug(f"Got message {type}")

        # ==================================================================
        # NEW_SESSION
        # 1. Create the directory structure for the session
        # 2. Set it to be the currently active session
        # 3. Add an entry to the sessions cache
        # 4. Purge old sessions if the number now exceeds max-sessions
        # ==================================================================

        if type == MsgType.NEW_SESSION :
            logging.debug("Received NEW_SESSION")
            self.current_session = msg.session
            await self.sessions_cache.new_session(msg.session)


        # ==================================================================
        # NEW_DETECTION
        # 1. Create the DetectionMetadata object and write the metadata json file
        # 2. Write the immage jpeg file
        # 3. Update the session cache by adding the detection to the session
        # ==================================================================
        elif type == MsgType.NEW_DETECTION :
            logging.debug("**** Received NEW_DETECTION ****")

            metadata = DetectionMetadata(
                self.current_session,
                msg.detection,
                msg.created,
                msg.created, #updated
                msg.score,
                msg.clazz,
                msg.width,
                msg.height,
            )
            await self.sessions_cache.new_detection(metadata, msg.img_data)

        # ==================================================================
        # UPDATE_DETECTION_META
        # 1. Update the metadata in the cache
        # 2. Overwrite the configuration in the metadata file
        # ==================================================================
        elif type == MsgType.UPDATE_DETECTION_META :
            await self.sessions_cache.update_detection_meta(msg.detection, msg.updated)

        # ==================================================================
        # UPDATE_DETECTION
        # 1. Update the metadata in the cache
        # 2. Overwrite the configuration in the metadata file
        # 3. Overwrite the image in the image file
        # ==================================================================
        elif type == MsgType.UPDATE_DETECTION :
            await self.sessions_cache.update_detection(
                msg.detection,
                msg.updated,
                msg.score,
                msg.width,
                msg.height,
                msg.img_data
            )

        # ==================================================================
        # PREVIEW_FRAME
        # ==================================================================
        elif type == MsgType.STREAM_FRAME :
            logging.debug("Got frame - sending it to image streamer")
            #await self.bluetooth_controller.image_streamer.addFrame(msg.timestamp, msg.frame)

        # ==================================================================
        # Active Flow
        # ==================================================================
        elif type == MsgType.ACTIVE_FLOW :
            logging.debug(f"Flow state message. flow = {ActiveFlow(msg.flow)}")
            self.active_flow = ActiveFlow(msg.flow)
            await self.state_stream.asend(self.active_flow)

        # Ignore unknown
        else :
            pass

    async def set_active_flow(self, flow):
        self.active_flow = flow
        msg = SetActiveFlowMessage(flow)
        await self.ipc_server.send(msg.to_proto())

    def get_active_flow(self):
        return self.active_flow

    def list_sessions(self):
        return self.sessions_cache.list_sessions()











