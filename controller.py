import multiprocessing
import os.path as path
import cv2
import lgsvl
import time
from logger import create_logger

class BaseController:
    def init(self):
        self.k = 0
        return {
            "throttle": 1.0,
            "braking": 0.0,
            "steering": 0.0
        }
    
    def execute(self, sensors, old_controls):
        self.k += 1
        return {
            "throttle": 1.0 + (self.k * 0.01),
            "braking": 0.0,
            "steering": 0.0
        }

class ControllerProcess(multiprocessing.Process):
    def __init__(self, log_q, queue, event_handler, sim_event_handler):
        super().__init__()
        self.log = create_logger(log_q, controller=True)
        self.queue = queue
        self.eventH = event_handler
        self.eventH_sim = sim_event_handler
        self.log.info("Initialized the controller")

        self.controller = BaseController()

    def run(self):
        old_controls = None
        self.log.info("Starting the controller process...")
        initial_controls = self.controller.init()
        self.queue.put(initial_controls)
        self.log.debug("Put initial controls to the queue")
        while True:
            self.log.debug("Setting the simulation event. Requesting sensor data and/or sending data.")
            self.eventH_sim.set()
            self.log.debug("Waiting for an event from the simulator")
            while not self.eventH.is_set():
                self.eventH.wait()
            self.log.debug("Received an event from the simulator")
            self.eventH.clear()
            sensors = self.queue.get()
            controls = self.controller.execute(sensors, old_controls)
            old_controls = controls
            self.queue.put(controls)
