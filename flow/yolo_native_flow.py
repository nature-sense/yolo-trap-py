import time

import cv2
import numpy as np

from picamera2 import Picamera2, MappedArray
from ultralytics import YOLO

from flow.detect_flow import DetectFlow

class YoloNativeFlow(DetectFlow):

    def __init__(self, max_tracking, min_score, sessions_directory, lores_size, main_size, model, session_manager):
        super().__init__(max_tracking, min_score, sessions_directory, lores_size, main_size, model, session_manager)

        #os.environ['LIBCAMERA_LOG_LEVELS'] = '4'
        self.picam2 = Picamera2()
        self.model = YOLO(model)

    def flow_task(self):
        print("FLOW TASK")
        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': self.main_size},
            lores={'format': 'RGB888', 'size': self.lores_size}
        )

        self.picam2.configure(camera_config)
        #self.picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0})  # 2.0})
        self.picam2.start(camera_config)

        while True:
            start_frame = time.perf_counter()
            request = self.picam2.capture_request()
            #print("GOT REQUEST")

            with MappedArray(request, 'lores') as l:
                with MappedArray(request, 'main') as m:
                    end_frame = time.perf_counter()

                    start_model = time.perf_counter()
                    results = self.model.track(l.array)
                    end_model = time.perf_counter()

                    print("frame = ", (end_frame-start_frame)*1000)
                    print("model = ", (end_model-start_model)*1000)

                    #current_datetime = datetime.now()
                    # current_timestamp_ms = int(current_datetime.timestamp() * 1000)

                    boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                    track_ids = [tid.item() for tid in results[0].boxes.id.int().cpu().numpy()]
                    scores = [s.item() for s in results[0].boxes.conf.numpy()]
                    classes = [c.item() for c in results[0].boxes.cls.numpy().astype(np.int32)]

                    annotated_frame = results[0].plot()
                    cv2.imwrite("img.jpg", annotated_frame)

                    self.save_detections(m, zip(boxes, track_ids, scores, classes))
                    request.release()

                    # cv2.imshow("Camera", annotated_frame)

                    # results = ncnn_model.track(source = m.array, stream=True, persist=True)
                    # for r in results:
                #    print(r.boxes)

