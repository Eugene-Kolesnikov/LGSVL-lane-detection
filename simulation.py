import lgsvl
from connection import Connection
import cv2
from os import path

from PIL import ImageFont, ImageDraw, Image

class Simulation:
    def __init__(self, config):
        self.config = config
        self.conn = Connection(config.get("SIMULATOR_HOST"),
                               config.get("SIMULATOR_PORT"))
        self.conn.connect()
        self.sim = self.conn.simulation()
        self.vehicle = None

        self.path = "/tmp"

        self.video = None

    def set_env(self, env):
        # Set the map
        MAP = env.get("map")
        if self.sim.current_scene == MAP:
            self.sim.reset()
        else:
            self.sim.load(MAP)

        # Set the time
        self.sim.set_time_of_day(env.get("time"))

        # Set the vehicle
        vehicleState = lgsvl.AgentState()
        vehicleState.transform = self.sim.get_spawn()[0]
        self.vehicle = self.sim.add_agent(env.get("car"),
                                          lgsvl.AgentType.EGO,
                                          vehicleState)
        self.vehiclePos = self.vehicle.state.position
        self.vehicle.connect_bridge(self.config.get("BRIDGE_HOST"),
                                    self.config.get("BRIDGE_PORT"))
        self.vehicle.on_collision(self._on_collision)

    def set_agents(self, agents):
        for agent in agents:
            agentPos = agent.get("pos")
            agentModel = agent.get("model")
            MAX_POV_SPEED = agent.get("MAX_POV_SPEED")
            POVState = lgsvl.AgentState()
            POVPos = lgsvl.Vector(
                self.vehiclePos.x + agentPos[0],
                self.vehiclePos.y + agentPos[1],
                self.vehiclePos.z + agentPos[2]
            )
            POVState.transform = self.sim.map_point_on_lane(POVPos)
            POV = self.sim.add_agent(agentModel, lgsvl.AgentType.NPC, POVState)
            POV.on_collision(self._on_collision)

            POV.follow_closest_lane(True, MAX_POV_SPEED, False)
    
    def start(self):
        import time
        _EXECUTION_TIME_ = 0.1
        c = lgsvl.VehicleControl()                                                      
        c.throttle = 104.5                                                         
        self.vehicle.apply_control(c, True)
        while True:
            self.sim.run(_EXECUTION_TIME_)
            # time.sleep(15)
            #sensors = self.vehicle.get_sensors()
            # print(sensors)
            self._get_sensors()

    def _on_collision(self, agent1, agent2, contact):
        if self.video:
            self.video.release()
        raise Exception("{} collided with {}: {}".format(
            agent1, agent2, contact
        ))

    def _get_sensors(self):
        state = self.vehicle.state
        print("Vehicle speed:", state.speed)
        for sensor in self.vehicle.get_sensors():
            print(sensor.name)
            if sensor.name == "Main Camera":
                img = self._get_image(sensor)
                img = self._add_speed(img, state.speed)
                if self.video is None:
                    self._init_video(img.shape)
                print(img.shape)
                self.video.write(img)
                cv2.imshow(sensor.name, img)
                cv2.waitKey(1)

    def _get_image(self, sensor):
        PATH = path.join(self.path, sensor.name + ".png")
        sensor.save(PATH, compression=0)
        image = cv2.imread(PATH)
        return image
    
    def _add_speed(self, img, speed):
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (10,50)
        fontScale = 1
        fontColor = (255,255,255)
        lineType = 2

        cv2.putText(img,f"Speed: {speed}", bottomLeftCornerOfText, 
            font, fontScale, fontColor, lineType)
        
        return img
    
    def _init_video(self, shape):
        self.video = cv2.VideoWriter('outpy.avi',
            cv2.VideoWriter_fourcc(*'mp4v'), 
            10, (shape[1],shape[0])) 