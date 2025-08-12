import logging
from abc import ABC, abstractmethod

import zmq
import zmq.asyncio

IP_ADDRESS = "127.0.0.1"
PORT = 1936

class IpcServer:
    def __init__(self, handler):
        self.handler = handler
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.PAIR)

    async def receiver_task(self):
        logging.debug("Starting ipc receiver task")
        self.sock.bind(f"tcp://{IP_ADDRESS}:{PORT}")

        while True:
            data = await self.sock.recv()  # waits for msg to be ready
            await self.handler.handle_message(data)

    async def send(self, data):
        await self.sock.send(data)

class MessageHandler(ABC) :
    @abstractmethod
    def handle_message(self, msg):
        pass

class IpcClient:
    def __init__(self, handler : MessageHandler):
        self.handler = handler
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.PAIR)
        self.sock.connect(f"tcp://{IP_ADDRESS}:{PORT}")

    async def receiver_task(self):
        while True:
            data = await self.sock.recv()  # waits for msg to be ready
            self.handler.handle_message(data)

    async def send(self, data):
        await self.sock.send(data)