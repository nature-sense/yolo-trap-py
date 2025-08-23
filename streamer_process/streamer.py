
from ffmpeg.asyncio import FFmpeg

video_format = "mp4"
server_url = "http://localhost:8083"

class Streamer :
    def __init__(self, width, height, fps):
        self.width = width
        self.height = height
        self.fps = fps
        self.process = (
            FFmpeg()
            .input('udp://127.0.0.1:8085', format = 'rawvideo', codec = "rawvideo", pix_fmt = 'rgb24', s = '{}x{}'.format(width, height))
            .output(
                url=server_url + '/stream',
                listen=1,  # enables HTTP server
                pix_fmt="yuv420p",
                preset="ultrafast",
                f=video_format
            )
        )

    async def streamer_task(self):
        await self.process.execute()

