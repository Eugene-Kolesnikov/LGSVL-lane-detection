import lgsvl
import cv2
from os import path
import time

from PIL import ImageFont, ImageDraw, Image

class Simulation:
    def __init__(self, global_config, connection_config, log, no_control, sync, output):
        self.log = log
        self.parameters = global_config
        self.config = connection_config
        self.no_control = no_control
        self.sync = sync

        self.log.debug("Creating the simulation")
        self.log.debug(f"Controller is '{'off' if self.no_control else 'on'}'")
        self.log.debug(f"Execution type: {'syncronous' if self.sync else 'asynchronous'}")

        self.log.debug("Connecting to {connection_config.get('SIMULATOR_HOST')}:{connection_config.get('SIMULATOR_PORT')}")
        self.sim = lgsvl.Simulator(connection_config.get("SIMULATOR_HOST"), connection_config.get("SIMULATOR_PORT"))
        self.log.debug("Initialized the simulation")
        self.vehicle = None

        self.start_time = None

        self.path = "/tmp"

        self.video = None
        self.video_file = output

        self.queue = None
        self.eventH = None
        self.eventH_control = None

    def set_env(self, env):
        # Set the map
        MAP = env.get("map")
        if self.sim.current_scene == MAP:
            self.sim.reset()
            self.log.debug(f"Reset the map: {MAP}")
        else:
            self.sim.load(MAP)
            self.log.debug(f"Loaded the map: {MAP}")

        # Set the time
        self.sim.set_time_of_day(env.get("time"))
        self.log.debug(f"Set the time to {env.get('time')}")

        # Set the vehicle
        vehicleState = lgsvl.AgentState()
        vehicleState.transform = self.sim.get_spawn()[0]
        self.vehicle = self.sim.add_agent(env.get("car"),
                                          lgsvl.AgentType.EGO,
                                          vehicleState)
        self.log.debug("Created an EGO vehicle: {env.get('car')}")
        self.vehiclePos = self.vehicle.state.position
        self.vehicle.connect_bridge(self.config.get("BRIDGE_HOST"),
                                    self.config.get("BRIDGE_PORT"))
        self.log.debug("Connected the vehicle to the bridge: {self.config.get('BRIDGE_HOST')}:{self.config.get('BRIDGE_PORT')}")
        self.vehicle.on_collision(self._on_collision)
        self.log.debug("Connected a collision callback")

    def set_agents(self, agents):
        for agent in agents:
            self.log.debug(f"Adding an agent: {agent}")
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
    
    def set_async(self, queue, control_event_handler, event_handler):
        self.queue = queue
        self.eventH = event_handler
        self.eventH_control = control_event_handler
    
    def start(self):
        _TOTAL_TIME_ = self.parameters.get("execution_time")
        _EXECUTION_TIME_STEP_ = 0.1
        self.log.debug(f"Total simulation time is set to {_TOTAL_TIME_} seconds")
        self.log.debug(f"Execution time-step is set to {_EXECUTION_TIME_STEP_} seconds")
        
        controls = lgsvl.VehicleControl()
        self.log.debug("Created vehicle controls")
        if self.no_control:
            controls.throttle = 1.0
            self.log.debug(f"The simulation without and automatic control sets throttle to {controls.throttle}")
        
        self.log.debug("Starting the simulation loop...")
        curTime = 0
        self.start_time = time.time()
        self.sim.run(0.01)
        while True:
            new_controls = None
            self.log.debug("Loading sensors from the server")
            sensors = self._get_sensors()
            self.log.debug("Loaded sensors from the server")
            if not self.no_control:
                new_controls = self._checkControlProcess(sensors)
            
            if new_controls:
                controls = self._updateControls(controls, new_controls)
                self.log.debug("Updating controls on the server")
                self.vehicle.apply_control(controls, True)

            frame = self._sensor_visualization(sensors, controls, curTime)
            self._save_frame(frame)
            self._visualize_frame(frame)

            self.log.debug(f"Running the simulation for {_EXECUTION_TIME_STEP_} seconds")
            self.sim.run(_EXECUTION_TIME_STEP_)
            curTime += _EXECUTION_TIME_STEP_
            self.log.info(f"Current execution time: {curTime}")
            if curTime >= _TOTAL_TIME_:
                self.log.info("Current execution time reached the limit. Quitting the simulation.")
                self.log.info(f"The simulation took {time.time() - self.start_time} seconds")
                break

    def _checkControlProcess(self, sensors):
        new_controls = None
        if self.sync:
            # Waiting for the controller process to send event
            self.log.debug("Waiting for an event from the control process")
            self.eventH.wait()
        if self.eventH.is_set():
            self.log.debug("Received an event from the control process")
            # The controller requested data and possibly returned controls.
            self.log.debug("The queue is not empty. Extracting new controls.")
            # The control queue is not empty: The control process returned controls.
            new_controls = self.queue.get()
            self.log.debug(f"Extracted controls: {new_controls}")
            self.log.debug("Unsetting the simulation event flag")
            self.eventH.clear()
            self.log.info("Sending sensors to the controller")
            self.queue.put(sensors)
            self.log.debug("Setting the control process event")
            self.eventH_control.set()
            #sent_sensors = True
        return new_controls#, sent_sensors

    def _updateControls(self, controls, new_controls):
        self.log.info("Updating controls for the simulation server")
        controls.throttle = new_controls.get("throttle")
        controls.braking = new_controls.get("braking")
        controls.steering = new_controls.get("steering")
        return controls

    def _on_collision(self, agent1, agent2, contact):
        if self.video:
            self.log.debug("Closing the video feed")
            self.video.release()
        self.log.error("{} collided with {}: {}".format(
            agent1, agent2, contact
        ))
        if self.start_time:
            self.log.info(f"The simulation took {time.time() - self.start_time} seconds")
        raise Exception("Emergency termination")

    def _get_sensors(self):
        sensors = {}
        sensors["speed"] = self.vehicle.state.speed
        for sensor in self.vehicle.get_sensors():
            if sensor.name == "Main Camera":
                img = self._get_image(sensor)
                sensors[sensor.name] = img
        return sensors

    def _get_image(self, sensor):
        self.log.debug(f"Loading camera image: {sensor.name}")
        PATH = path.join(self.path, sensor.name + ".png")
        sensor.save(PATH, compression=0)
        self.log.debug(f"Downloaded image from the server to '{PATH}'")
        image = cv2.imread(PATH)
        return image
    
    def _sensor_visualization(self, sensors, controls, curTime):
        img = sensors.get("Main Camera")
        img = self._add_time(img, curTime)
        img = self._add_speed(img, sensors.get("speed"))
        img = self._add_controls(img, controls)
        return img

    def _save_frame(self, frame):
        if self.video is None:
            shape = frame.shape
            self.log.debug("Initializing a video writer")
            self.video = cv2.VideoWriter(self.video_file, cv2.VideoWriter_fourcc(*'mp4v'),
                10, (shape[1], shape[0]))
        self.log.debug("Writing the frame to the video file")
        self.video.write(frame)
    
    def _visualize_frame(self, frame):
        cv2.imshow("Simulation", frame)
        cv2.waitKey(1)
    
    def _add_time(self, img, curTime):
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (10,50)
        fontScale = 1
        fontColor = (255,255,255)
        lineType = 2

        cv2.putText(img,f"Time: {curTime}", bottomLeftCornerOfText, 
            font, fontScale, fontColor, lineType)
        
        return img
    
    def _add_speed(self, img, speed):
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (10,100)
        fontScale = 1
        fontColor = (255,255,255)
        lineType = 2

        cv2.putText(img,f"Speed: {speed}", bottomLeftCornerOfText, 
            font, fontScale, fontColor, lineType)
        
        return img
    
    def _add_controls(self, img, controls):
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (10,150)
        fontScale = 1
        fontColor = (255,255,255)
        lineType = 2

        cv2.putText(img,f"Throttle: {controls.throttle}", bottomLeftCornerOfText, 
            font, fontScale, fontColor, lineType)
        
        return img
