
import asyncio
import logging

from flow.yolo_native_flow import YoloNativeFlow
from control.control_service import ControlService

from flow.yolo_preview_flow import YoloPreviewFlow

#YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
#IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
#NCNN_MODEL = "./models/insects_320_ncnn_model"
NCNN_MODEL = "./models/insects_320_ncnn_model"

SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
CACHE_SIZE = 20
MIN_SCORE = 0.5

MAIN_SIZE = (2028, 1520)
#MAIN_SIZE = (4608, 2592)

LORES_SIZE = (320,320)
#LORES_SIZE = (640,640)

PREVIEW_SIZE = (320,240)

def run_detection() :
    yolo_detect_flow = YoloNativeFlow(
        min_score=0.5,
        lores_size=LORES_SIZE,
        main_size=MAIN_SIZE,
        max_tracking=MAX_TRACKING,
        model=NCNN_MODEL
    )
    yolo_detect_flow.flow_task()

def run_preview() :
    yolo_preview_flow = YoloPreviewFlow(
        main_size=PREVIEW_SIZE,
    )
    yolo_preview_flow.stream_task()

async def main() :
    logger = logging.getLogger()

    print(f"Yolo Trap starting")
    loop = asyncio.get_event_loop()

    control = ControlService(run_detection, run_preview)
    await control.run(loop)

if __name__ == "__main__":
    asyncio.run(main())