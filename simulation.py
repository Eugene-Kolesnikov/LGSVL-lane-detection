import lgsvl
from connection import Connection


class Simulation:
    def __init__(self, config):
        self.config = config
        self.conn = Connection(config.get("SIMULATOR_HOST"),
                               config.get("SIMULATOR_PORT"))
        self.conn.connect()
        self.sim = self.conn.simulation()
        self.vehicle = None

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
        for agent in agents.get("agents"):
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

    def get_vehicle(self):
        conn = Connection(self.config.get("SIMULATOR_HOST"),
                          self.config.get("SIMULATOR_PORT"),
                          self.vehicle.uid)
        return conn

    def start(self):
        import time
        while True:
            self.sim.run(0.05)
            # time.sleep(15)
            # sensors = self.vehicle.get_sensors()
            # print(sensors)

    def _on_collision(self, agent1, agent2, contact):
        raise Exception("{} collided with {}: {}".format(
            agent1, agent2, contact
        ))
