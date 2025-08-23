import asyncudp
from aioreactive import AsyncSubject, AsyncAnonymousObserver

class FramePublisher :
    def __init__(self):
        self.sock = None
        self.channel = AsyncSubject()

    async def run_client(self) :
        try :
            self.sock = await asyncudp.create_socket(remote_addr=('127.0.0.1', 8003))

            async def del_session_sink(s):
                await self.sock.sendto(s)
            sink = AsyncAnonymousObserver(del_session_sink)
            await self.channel.subscribe_async(sink)

        except Exception as e:
            self.sock.close()

