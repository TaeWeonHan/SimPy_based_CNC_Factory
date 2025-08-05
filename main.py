# main.py
import simpy
import random
from base_Customer import Customer
from manager import Manager
from log_SimPy import Logger
from config_SimPy import *
from base_Store import ItemStore


def run_simulation(sim_duration=SIM_TIME):
    """Run the manufacturing simulation"""
    print("================ Manufacturing Process Simulation ================")

    # Setup simulation environment
    env = simpy.Environment()

    # Create logger with env
    logger = Logger(env)

    # Create manager and provide logger
    manager = Manager(env, logger)

    # Create customer to generate orders
    Customer(env, manager, logger)

    # Run simulation
    print("\nStarting simulation...")
    print(f"Simulation will run for {sim_duration} minutes")

    # Run simulation
    env.run(until=sim_duration)
    
if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)

    # Run the simulation
    run_simulation()