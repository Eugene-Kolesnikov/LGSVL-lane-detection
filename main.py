import json
from simulation import Simulation
from controller import Controller

SIMULATION_CONFIG = "config/simulation.json"
ENVIRONMENT_CONFIG = "config/environment.json"
AGENTS_CONFIG = "config/agents.json"


def read_config(path):
    try:
        with open(path, 'rt') as f:
            config = json.load(f)
            return config
    except Exception:
        raise


def main():
    global SIMULATION_CONFIG
    global ENVIRONMENT_CONFIG
    global AGENTS_CONFIG

    simulation_config = read_config(SIMULATION_CONFIG)
    sim = Simulation(simulation_config)

    env_config = read_config(ENVIRONMENT_CONFIG)

    agents_config = read_config(AGENTS_CONFIG)

    sim.set_env(env_config)
    sim.set_agents(agents_config)

    vehicle = sim.get_vehicle()

    controller = Controller(vehicle)

    controller.start()

    # Blocking operation
    sim.start()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception occured:", e)
        raise
