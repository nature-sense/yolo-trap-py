import time

import cv2

from picamera2 import MappedArray, Picamera2, CompletedRequest
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics)
from deep_sort_realtime.deepsort_tracker import DeepSort
from streamerate import stream

from flow.detect_flow import DetectFlow

last_detections = []

class Imx500Flow(DetectFlow) :
    def __init__(self, max_tracking, min_score, sessions_directory, lores_size, main_size, model):
        super().__init__(max_tracking, min_score, sessions_directory, lores_size, main_size, model)
        self.imx500 = IMX500(self.model)
        self.picam2 = Picamera2(self.imx500.camera_num)
        self.tracker = DeepSort(max_age=50)

    def flow_task(self):
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
        intrinsics.labels = ["insect]"]
        intrinsics.update_with_defaults()

        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': self.main_size},
            # lores={'format': 'RGB888', 'size': (320, 320)},
            buffer_count=12
        )
        self.picam2.configure(camera_config)
        self. picam2.start(camera_config, show_preview=False)
        print("Camera started")
        while True:
            start_frame = time.perf_counter()
            request: CompletedRequest = self.picam2.capture_request()
            metadata = request.get_metadata()
            end_capture = time.perf_counter()
            print("camera = ", (end_capture - start_frame) * 1000, "ms")

            np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
           # input_w, input_h = self.imx500.get_input_size()

            if np_outputs is not None:
                with (MappedArray(request, 'main') as frame):

                    detections = stream(zip(np_outputs[0][0],np_outputs[1][0],np_outputs[2][0])).\
                        filter(lambda c : c[1] > self.min_score).toList()
                    boxes = stream(detections).map(lambda d : (d[0].tolist(), d[1], "insect")).toList()

                    start = time.perf_counter()
                    tracks = self.tracker.update_tracks(boxes, frame=frame.array)
                    track_ids = stream(tracks).map(lambda t : t.track_id).toList()
                    end = time.perf_counter()
                    print("duration = ", (end - start) * 1000, "ms")

                    detections = stream(zip(detections,tracks)).\
                        map(lambda e : (e[0][0], int(e[1].track_id), e[0][1], int(e[0][2]))).toList()

                    #print(*temp)

                    self.save_detections(frame, detections)

                    end_frame = time.perf_counter()
                    duration = end_frame - start_frame
                    print("frame = ", duration * 1000, "ms or " + str(1/duration) + " fps")

                    #boxes = np_outputs[0][0]
                    #scores = np_outputs[1][0]
                    #classes = np_outputs[2][0]

                    #scaled_box = self.scale(boxes[0])
                    # print("scaled-box", scaled_box)
                    #x0, y0, x1, y1 = scaled_box
                    #crop = frame.array[y0:y1, x0:x1]
                    #cv2.imwrite("crap.jpg", crop)

                # print(boxes)
                i = 0
                # boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                # track_ids = results[0].boxes.id.int().cpu().numpy().astype(np.int32)
                # scores = results[0].boxes.conf.numpy()
                # classes = results[0].boxes.cls.numpy().astype(np.int32)

                #for score in scores:
                #    # print(score)
                #    if score > 0.55:
                #        detections.append(Detection(boxes[i], classes[i], scores[i]))
                #    i = i + 1
                #if len(detections) != 0:
                # request.save("raw", "raw.jpg")

                with (MappedArray(request, 'main') as main):
                    cv2.imwrite('../../main.jpg', main.array)
            request.release()

    def track(self, frame, boxes):
        tracks = self.tracker.update_tracks(boxes, frame=frame)

