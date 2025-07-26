import zmq
import zmq.asyncio

IP_ADDRESS = "127.0.0.1"
PORT = 1337

class SessionIpcServer:
    def __init__(self, session_server):
        self.session_server = session_server
        self.ctx = zmq.asyncio.Context()

    async def server_task(self):
        sock = self.ctx.socket(zmq.PAIR)
        sock.bind(f"tcp://{IP_ADDRESS}:{PORT}")
        while True:
            data = await sock.recv()  # waits for msg to be ready

            await self.session_server.handle_message(data)


class SessionIpcClient:
    def __init__(self):
        self.ctx = zmq.asyncio.Context()
        self.sock = self.ctx.socket(zmq.PAIR)
        self.sock.connect(f"tcp://{IP_ADDRESS}:{PORT}")

    def send(self, data):
        self.sock.send(data)
