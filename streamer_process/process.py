import asyncio
import logging

from streamer_process.streamer import Streamer

class StreamerProcess :

    def __init__(self, settings):
        self.settings = settings

    async def start_services(self):
        logging.debug("Starting streamer services")

        streamer = Streamer(320,320,30)
        await asyncio.gather(streamer.streamer_task())