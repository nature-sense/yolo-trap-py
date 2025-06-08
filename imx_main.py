
import asyncio

from flow.imx500_flow import Imx500Flow
from bluetooth import BluetoothControl

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
SESSIONS_DIRECTORY = "../sessions"
MAX_TRACKING = 10
MIN_SCORE = 0.5

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)

def run_detection() :
    imx_detect_flow = Imx500Flow(
        max_tracking = 10,
        min_score = 0.5,
        sessions_directory = SESSIONS_DIRECTORY,
        lores_size = LORES_SIZE,
        main_size = MAIN_SIZE,
        model = IMX_MODEL
    )

    imx_detect_flow.flw_task()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    control = BluetoothControl(run_detection)
    loop.run_until_complete(control.run(loop))

main()