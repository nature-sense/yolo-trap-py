import os
from abc import ABC, abstractmethod
#from session import Session

class DetectFlow(ABC):

    def __init__(self, max_tracking, min_score, sessions_directory, lores_size, main_size, model, session_manager):
        os.environ['LIBCAMERA_LOG_LEVELS'] = '4'
        self.session_manager = session_manager

        self.session = session_manager.new_session()
        self.min_score = min_score
        self.lores_size = lores_size
        self.main_size = main_size
        self.model = model

    @abstractmethod
    def flow_task(self):
        pass

    def save_detections(self, frame, detections):
        for box, track_id, score, clazz in detections:

            scaled_box = self.scale(box)
            print("scaled-box", scaled_box)
            x0, y0, x1, y1 = scaled_box
            img_width = x1-x0
            img_height = y1-y0

            # print("timestamp", current_timestamp_ms)
            # print("box", box)
            # print("track-id", track_id)
            # print("score", score)
            # print("class", clazz)

            save_image = self.session.set_entry(track_id, score, clazz, img_width, img_height)
            self.session.save_metadata(track_id)

            if save_image:
                scaled_box = self.scale(box)
                print("scaled-box", scaled_box)
                x0, y0, x1, y1 = scaled_box
                crop = frame.array[y0:y1, x0:x1]
                self.session.save_image(track_id, crop)
                #cv2.imwrite(f"crop{track_id}.jpg", crop)


    def scale(self, rect):
        s_w, s_h = self.lores_size
        d_w, d_h = self.main_size
        x0, y0, x1, y1 = rect
        x_scale = d_w / s_w
        y_scale = d_h / s_h
        return int(x0 * x_scale), int(y0 * y_scale), int(x1 * x_scale), int(y1 * y_scale)