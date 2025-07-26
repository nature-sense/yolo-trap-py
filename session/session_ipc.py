import asyncio
import zmq
import zmq.asyncio



class ZmqIpcServer:
    def __init__(self, session_server):
        self.session_server = session_server
        self.ctx = zmq.asyncio.Context()



    async def run_server(self):
        self.server.bind((IP_ADDRESS, PORT))
        self.server.listen(1)
        self.server.setblocking(False)

        while True :
            client_socket, _ = await self.loop.sock_accept(self.server)
            while True:
                try:
                    data = await self.loop.sock_recv(client_socket, 131072)
                    if not data:
                        break
                    await self.session_server.handle_message(data)
                    #print(f"Received: {data.decode()}")
                except ConnectionResetError:
                    break
            client_socket.close()
            #break





