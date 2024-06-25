from ultralytics import YOLO
import cv2
import numpy as np
import threading
import pydirectinput
import time

from .aim import Aim
from .logger import logger
from .monitor_keyboard import Monitor_Keyboard


class Model(threading.Thread):
    # global will_end,status
    def __init__(self, aim: Aim, mk:Monitor_Keyboard, model_path:str = "yolov8n.pt") -> None:
        super().__init__()
        # self.model = YOLO("yolov8n.pt")
        if model_path == None:
            model_path = "yolov8n.pt"
        self.model = YOLO(model_path)
        self.aim = aim
        self.cap = cv2.VideoCapture(1)
        self.mk = mk
        logger.info("Model inited")
        self.cnt = 0
        self.last_time = time.time()

    def run(self):
        # global will_end,status
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            # result = self.model.track(
            #     frame,
            #     show=False,
            #     persist=True,
            #     tracker="bytetrack.yaml",
            #     conf=0.2,
            #     classes=[
            #         0,
            #     ],
            #     verbose=False,
            # )
            result = self.model.predict(
                frame,
                show = False,
                conf = 0.4,
                classes = [0,1],
                verbose = False
            )
            xywh = result[0].boxes.xywh
            ids = result[0].boxes.id
            clses = result[0].boxes.cls
            confs = result[0].boxes.conf

            self.cnt+=1
            if self.cnt > 100:
                now = time.time()
                fps = self.cnt / (now-self.last_time) 
                self.cnt = 0
                self.last_time = now
                logger.info("FPS: {}".format(int(fps)))

            if self.mk.status:
                self.aim.update(xywh, clses, confs)

            cx = self.aim.cx
            cy = self.aim.cy
            id = self.aim.id

            annotated_frame: np.ndarray = result[0].plot(
                im_gpu=False, font_size=3, line_width=1
            )
            cv2.circle(annotated_frame, (320, 240), 1, (0, 255, 0), 5)
            cv2.circle(annotated_frame, (int(cx), int(cy)), 1, (255, 0, 0), 5)
            cv2.imshow("test", annotated_frame)
            cv2.waitKey(1)

            # logger.info(
            #     "\rframe height:{}\t width:{}\tfps:{}\tcx:{}\tcy:{}\tstatus:{}\toffset:{}\tid:{}\tpos:{}\tspeed:{}".format(
            #         height,
            #         width,
            #         fps,
            #         int(cx),
            #         int(cy),
            #         self.mk.status,
            #         self.mk.offset,
            #         id,
            #         pydirectinput.position(),
            #         list(map(lambda x: int(result[0].speed[x]), result[0].speed)),
            #     )
            # )

            # if self.mk.status:
            #     self.aim.update(xywh, clses, confs)

            if self.mk.will_end:
                logger.info("aimbot end")
                self.aim.end()
                break
            
        self.cap.release()
        cv2.destroyAllWindows()
