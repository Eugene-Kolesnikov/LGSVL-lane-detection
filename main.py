import json

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

#TODO:
# - Add output file to cmd
# - Add log file to cmd
# - Add controller support

def main(args, log):
    config = read_config(args.config[0])
    log.info(f"Parsed the config file: {config}")

    sim = Simulation(config.get("global"), config.get("connection"), log, args.no_controller, args.synchronous)
    log.info("Created a simulation, connected to the server")
    sim.set_env(config.get("environment"))
    log.info("Created an environment")
    sim.set_agents(config.get("agents"))
    log.info("Created agents")

    log.info("Starting the simulation...")
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

def launch_logger():
    import logging
    import queue
    from logging.handlers import QueueHandler, QueueListener
    from datetime import datetime

    # Get queue
    q = queue.Queue(-1)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)-8s: %(message)s')

    # create file handler which logs even debug messages
    fh = logging.FileHandler(f"{datetime.now()}.log")
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    
    # Start queue listener using the stream handler above
    ql = QueueListener(q, fh, ch, respect_handler_level=True)
    ql.start()

    # Create log and set handler to queue handle
    log = logging.getLogger('simulation')
    log.setLevel(logging.DEBUG) # Log level = DEBUG
    qh = QueueHandler(q)
    log.addHandler(qh)

    log.info('Initialized the logger')

    return log, ql

if __name__ == "__main__":
    try:
        log, ql = launch_logger()
    except Exception as e:
        print("Was not able to launch a logger...")
        print(e)
        quit()
    
    try:
        args = parse_args()
        log.info(f"Parsed the console arguments: {args}")
        main(args, log)
        ql.stop()
    except Exception as e:
        log.error(e)
        ql.stop()
