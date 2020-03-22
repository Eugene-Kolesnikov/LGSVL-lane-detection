import json
import logging
import argparse
from simulation import Simulation
from controller import Controller


# Read and parse a configuration file
def read_config(path):
    try:
        with open(path, 'rt') as f:
            config = json.load(f)
            return config
    except Exception: 
        raise


def main(args):
    config = read_config(args.config[0])

    sim = Simulation(config.get("connection"))
    sim.set_env(config.get("environment"))
    sim.set_agents(config.get("agents"))

    sim.start()
    """
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
    """

def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    
    parser.add_argument('config', metavar='config', type=str, nargs=1,
                    help='path to the configuration file')
    
    parser.add_argument('--no-controller', dest='no_controller', action='store_true',
                    help='run the simulation without the automatic controller')
    
    parser.add_argument('--synchronous', dest='synchronous', action='store_true',
                    help='run the simulation in sync with the controller')
    
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_args()
        main(args)
    except Exception as e:
        print("Exception occured:", e)
        raise
