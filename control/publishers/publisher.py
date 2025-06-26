import logging
from abc import ABC

import asyncio

class Publisher(ABC) :
    def __init__(self, bluetooth_server, service, characteristic):
        self.bluetooth_server = bluetooth_server
        self.service = service
        self.characteristic = characteristic
        self.notif_queue = asyncio.Queue()
        self.tasks = set()
        self.logger = logging.getLogger(name=__name__)

    async def start(self):
        task = asyncio.create_task(self.publish())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def publish(self):
        characteristic = self.bluetooth_server.get_characteristic(self.characteristic)

        while True:
            msg = await self.notif_queue.get()
            characteristic.value = msg
            result = self.bluetooth_server.update_value(self.service, self.characteristic)
