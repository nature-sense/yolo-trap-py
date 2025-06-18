import asyncio
import socket
from logging import Logger

IP_ADDRESS = "127.0.0.1"
PORT = 1337

class IpcServer:
    def __init__(self, session_server):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.session_server = session_server
        self.loop = asyncio.get_event_loop()


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


class IpcClient:
    def __init__(self):
        while True:
            try :
                self.socket = socket.create_connection((IP_ADDRESS, PORT))
                break
            except socket.error as error:
                print("Socket error ",error )

        print("Socket connected")

    def send(self, data):
        self.socket.send(data)

