class BaseController:
    def __init__(self, log):
        self.log = log
    
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