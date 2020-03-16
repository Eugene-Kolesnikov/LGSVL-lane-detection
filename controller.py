import multiprocessing
import os.path as path
import cv2
import lgsvl
import time


class Controller(multiprocessing.Process):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.conn.connect()
        self.vehicle = self.conn.get_vehicle()
        print(self.vehicle.uid)
        # print("UID:", vehicle.uid)
        self.path = "/tmp"

    def run(self):
        print("Started the controller")
        time.sleep(2)
        self.conn.conn.reset()
        print("Finished sleeping")
        controls = lgsvl.VehicleControl()
        while True:
            print("Loop")
            image = None
            print("Requesting sensors")
            try:
                sensors = self.vehicle.get_sensors()
                print("Received sensors")
                for sensor in sensors:
                    print(sensor.name)
                    if sensor.name == "Main Camera":
                        image = self._get_image(sensor)
            except Exception as e:
                print(e)
            if image:
                print("Showing image")
                cv2.imshow("Main Camera", image)
                cv2.waitKey(1)

            controls.throttle = 1
            self.vehicle.apply_control(controls, True)

    def _get_image(self, sensor):
        PATH = path.join(self.path, sensor.name + ".png")
        sensor.save(PATH, compression=0)
        image = cv2.imread(PATH)
        return image
