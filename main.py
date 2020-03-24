import json
import multiprocessing as mp
import argparse
from simulation import Simulation
from controller import ControllerProcess
from logger import launch_logger_listener, create_logger


# Read and parse a configuration file
def read_config(path):
    try:
        with open(path, 'rt') as f:
            config = json.load(f)
            return config
    except Exception: 
        raise


def main(args, log, log_q):
    config = read_config(args.config)
    log.info(f"Parsed the config file: {config}")

    sim = Simulation(config.get("global"), config.get("connection"), log, args.no_controller, args.synchronous, args.output)
    log.info("Created a simulation, connected to the server")
    sim.set_env(config.get("environment"))
    log.info("Created an environment")
    sim.set_agents(config.get("agents"))
    log.info("Created agents")

    if not args.no_controller:
        control_queue = mp.Queue(1)
        log.debug("Initialized the control queue")
        control_event = mp.Event()
        log.debug("Initialized the control event handler")
        sim_event = mp.Event()
        log.debug("Initialized the simulation event handler")

        sim.set_async(control_queue, control_event, sim_event)
        controller = ControllerProcess(log_q, control_queue, control_event, sim_event)
        controller.start()

    log.info("Starting the simulation...")
    try:
        sim.start()
    except Exception:
        pass
    controller.terminate()


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    
    parser.add_argument('config', metavar='config', type=str, nargs=1,
                    help='path to the configuration file')
    
    parser.add_argument('--no-controller', dest='no_controller', action='store_true',
                    help='run the simulation without the automatic controller')
    
    parser.add_argument('--synchronous', dest='synchronous', action='store_true',
                    help='run the simulation in sync with the controller')
    
    parser.add_argument('-o', '--output', metavar='output', type=str, nargs=1,
                    default=["monitor.avi"], help="path to the output monitor video file")
    
    parser.add_argument('-l', '--log', metavar='log', type=str, nargs=1,
                    default=["simulation.log"], help="path to the log file")
    
    args = parser.parse_args()
    args.config = args.config[0]
    args.output = args.output[0]
    args.log = args.log[0]

    return args


if __name__ == "__main__":
    try:
        args = parse_args()
        q, ql = launch_logger_listener(args.log)
        log = create_logger(q)
    except Exception as e:
        print("Was not able to launch a logger...")
        print(e)
        quit()
    
    try:
        log.info(f"Parsed the console arguments: {args}")
        main(args, log, q)
        ql.stop()
    except Exception as e:
        log.error(e)
        ql.stop()
