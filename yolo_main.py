
import asyncio

from session.session_manager import SessionManager
from flow.yolo_native_flow import YoloNativeFlow
from bluetooth.bluetooth_control import BluetoothControl

YOLO_MODEL = "/home/aidev/yolo-trap-py/models/best.pt"
IMX_MODEL = "/home/aidev/yolo-trap-py/models/network.rpk"
NCNN_MODEL = "/home/aidev/yolo-trap-py/models/best_ncnn_model"

SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
MAX_SESSIONS = 2
CACHE_SIZE = 20
MIN_SCORE = 0.5

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)

def run_detection(session_manager) :
    yolo_detect_flow = YoloNativeFlow(
        max_tracking=10,
        min_score=0.5,
        sessions_directory=SESSIONS_DIRECTORY,
        lores_size=LORES_SIZE,
        main_size=MAIN_SIZE,
        model=NCNN_MODEL,
        session_manager=session_manager
    )
    yolo_detect_flow.flow_task()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    session_manager = SessionManager(MAX_SESSIONS,  CACHE_SIZE, SESSIONS_DIRECTORY)
    control = BluetoothControl(run_detection, session_manager)
    loop.run_until_complete(control.run(loop))


