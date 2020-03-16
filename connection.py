import lgsvl


class Connection:
    def __init__(self, host, port, vehicleID=None):
        self.host = host
        self.port = port
        self.vehicleID = vehicleID
        self.conn = None
        self.vehicle = None

    def connect(self):
        self.conn = lgsvl.Simulator(self.host, self.port)
        if self.vehicleID:
            self.vehicle = lgsvl.agent.EgoVehicle(self.vehicleID, self.conn)
            self.conn.agents[self.vehicleID] = self.vehicle
            # self.vehicle.connect_bridge("127.0.0.1", 9090)

    def simulation(self):
        return self.conn

    def get_vehicle(self):
        if self.vehicle:
            return self.vehicle
