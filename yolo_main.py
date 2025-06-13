
import asyncio
from flow.yolo_native_flow import YoloNativeFlow
from control.control_service import ControlService
import picologging as logging

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
NCNN_MODEL = "/home/aidev/yolo-trap-py/models/best_ncnn_model"

SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
CACHE_SIZE = 20
MIN_SCORE = 0.5

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)

def run_detection() :
    yolo_detect_flow = YoloNativeFlow(
        min_score=0.5,
        lores_size=LORES_SIZE,
        main_size=MAIN_SIZE,
        max_tracking=MAX_TRACKING,
        model=NCNN_MODEL
    )
    yolo_detect_flow.flow_task()

async def main() :
    logging.basicConfig()
    logger = logging.getLogger()

    logger.info("Yolo Trap starting")
    loop = asyncio.get_event_loop()

    control = ControlService(run_detection)
    await control.run(loop)

if __name__ == "__main__":
    asyncio.run(main())