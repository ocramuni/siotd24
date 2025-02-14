import libcamera
from picamera2 import Picamera2
from ultralytics import YOLO

import utils

class Camera:
    def __init__(self):
        # Get configuration
        camera_model = utils.read_config('camera', 'Model')
        output_width = int(utils.read_config('camera', 'OutputSizeWidth'))
        output_height = int(utils.read_config('camera', 'OutputSizeHeight'))
        # Start-up camera
        tuning = Picamera2.load_tuning_file(f"{camera_model}_noir.json", dir='/usr/share/libcamera/ipa/rpi/vc4/')
        self.camera = Picamera2(tuning=tuning)
        camera_config = self.camera.create_still_configuration(
            main={'format': "RGB888", 'size': (1280, 720)},
            sensor={'output_size': (output_width, output_height), 'bit_depth': 10},
            controls={
                "AwbEnable": True,
                "AwbMode": libcamera.controls.AwbModeEnum.Auto,
            })
        self.camera.configure(camera_config)
        self.camera.start()
        # Load a YOLO11n NCNN model
        self.ncnn_model = YOLO("yolo11n_ncnn_model", task='detect')

    def get_picture(self):
        """Get a frame from the camera and detect people.

        Returns: frame as a numpy array and number of detected people.
        """
        frame = self.camera.capture_array("main")
        # looking for people only
        # class 0 = person
        results = self.ncnn_model.predict(frame, classes=(0))
        boxes = results[0].boxes
        # boxes.cls = class ID tensor representing category predictions
        return results[0].plot(), len(boxes.cls)
