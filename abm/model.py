from abm.consumer_agent import ConsumerAgent
from abm.prosumer_agent import ProsumerAgent
from abm.household import Household
import json 
import pandas as pd
import os
import numpy as np 

class Market:
    def __init__(self, config):
        # Global Variables for accurately calculating solar production from fixed tilt arrays
        self.latitude = 20.77 
        self.longitude = 156.92
        self.local_time_meridian = 150.0


        self.sim_config = config # simulation configuration for one run. 
        #households 
        self.households  = [] #probably going to hold everything 

        # Area of benchmark house which represents residential hourly demand
        self.benchmark_area = 2023.0 

        # Retail Electricity Rate --> Also used as the penalty rate
        self.retail_rate = 0.351
        # Avoided Fuel Cost Rate
        self.avoided_fuel_cost_rate = 0.0932

        # Date and Time Configuration
        self.days_in_month = 30  # Matches the production and consumption data we have
        self.minutes_in_month = self.days_in_month * 24 * 60
        self.hours_in_month = self.days_in_month * 24
        self.day_light_savings = False
        self.begin_month_day = 244

        # Internal State Variables
        self.initialized = False
        self.minute = 0
        self.increment = 60
        self.current_increment = 1
        self.number_increments = self.minutes_in_month // self.increment
        
        # Simulation Configuration
        self.storage_sim = 1
        self.forecasting_method = 0
        self.lag_increments = 1
        self.number_houses = 25 #Number of household agents within the simulation
        self.simulation_steps = 20 
        
        # Arrays and Matrices for Simulation Data
        self.annual_elec_savings = [0.0] * self.simulation_steps
        self.cumulative_elec_savings = [0.0] * self.simulation_steps
        self.total_adopters = [0] * self.simulation_steps
        self.cumulative_peak_capacity = [0.0] * self.simulation_steps
        self.seller_history = [[[0.0, 0.0, 0.0] for _ in range(self.number_increments)] for _ in range(self.number_houses)]
        self.buyer_history = [[[0.0, 0.0] for _ in range(self.number_increments)] for _ in range(self.number_houses)]
        self.overproduction = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.shortfall = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.overbought = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.underbought = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.daytime_demand = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.excess_solar = [[0.0] * self.number_increments for _ in range(self.number_houses)]
        self.interval_average_seller_price = [0.0] * self.number_increments
        self.running_average_seller_price = [0.0] * self.number_increments

    def print_initialization(self): 

        print(f"Latitude: {self.latitude}")
        print(f"Longitude: {self.longitude}")
        print(f"Local Time Meridian: {self.local_time_meridian}")
        print(f"Benchmark Area: {self.benchmark_area}")
        print(f"Retail Rate: {self.retail_rate}")
        print(f"Avoided Fuel Cost Rate: {self.avoided_fuel_cost_rate}")
        print(f"Days in Month: {self.days_in_month}")
        print(f"Minutes in Month: {self.minutes_in_month}")
        print(f"Hours in Month: {self.hours_in_month}")
        print(f"Day Light Savings: {self.day_light_savings}")
        print(f"Begin Month Day: {self.begin_month_day}")
        print(f"Initialized: {self.initialized}")
        print(f"Minute: {self.minute}")
        print(f"Increment: {self.increment}")
        print(f"Current Increment: {self.current_increment}")
        print(f"Number of Increments: {self.number_increments}")
        print(f"Storage Simulation Option: {self.storage_sim}")
        print(f"Forecasting Method: {self.forecasting_method}")
        print(f"Lag Increments: {self.lag_increments}")
        print(f"Number of Houses: {self.number_houses}")
        print(f"Simulation Steps: {self.simulation_steps}")

        print(f"Annual Electricity Savings: {self.annual_elec_savings}")
        print(f"Cumulative Electricity Savings: {self.cumulative_elec_savings}")
        print(f"Total Adopters: {self.total_adopters}")
        print(f"Cumulative Peak Capacity: {self.cumulative_peak_capacity}")
        print(f"Interval Average Seller Price: {self.interval_average_seller_price}")
        print(f"Running Average Seller Price: {self.running_average_seller_price}")

        print(f"seller_history = {self.seller_history}")
        print(f"buyer_history = {self.buyer_history}")
        print(f"shortfall = {self.shortfall}")
        print(f"overproduction = {self.overproduction}")


   

    def initialize_households(self):
        """ 
        Initialize the parameters of the households. Note, the model stores each
        household within a list class variable called self.households.

        INPUTS: 
            None

        RETURN: 
            None 
        """
        # Initialize households and demand ledgers
        household_configs = self.sim_config["household_params"]
        total_houses = len(household_configs)
        self.households = []
        demandLedger = np.zeros((total_houses, self.hours_in_month))
        demandLedgerMinutely = np.zeros((total_houses, self.hours_in_month * 60))

        
        hourly_cons_arr = self.load_hourly_consumption()
        # Converts DataFrame column to Series
        hourly_demand_series = hourly_cons_arr['hourly_consumption'].squeeze()  

        print(hourly_demand_series.shape)
        # Combined initialization loop
        for i, hh_config in enumerate(household_configs):
            index = hh_config["Index"]
            has_pv = hh_config["hasPV"]
            floor_area = hh_config["Floor Area"]
            wta = hh_config["WTA"]
            wtp = hh_config["WTP"]
            
            # Create household object
            household_obj = Household(index, has_pv, floor_area, wta, wtp)
            
            # Calculate hourly demand scaled by floor area
            demandLedger[i] = (hourly_demand_series / self.benchmark_area) * floor_area
            
            #NOTE: 
            #This for loop sets the value of hourly demand 
            #to each minute, as opposed to dividing by 60 
            #this is an artifact of the original java code
            #later in forecast energy demand, the individual values are divided by 60
            #which is also inefficient, but will be updated in a refactoring.
            for j in range(self.hours_in_month):
                start_minute = j * 60
                end_minute = start_minute + 60
                demandLedgerMinutely[i, start_minute:end_minute] = demandLedger[i][j] 
            
            #we set their minutely use
            household_obj.set_electricity_use(demandLedgerMinutely[i]) 
            
            self.households.append(household_obj)


            
    def run_simulation(self): 
        """  
        #TODO: update as you go:
        Initializes households prosumers and consumers and then runs the entire 
        simulation for self.number_increments timesteps.

        INPUT: 
        
        RETURN: 
            NONE
        
        """
        print(f"-"*50, "RUN SIMULATION", f"-"*50)
        print(f"")

        self.initialize_households2()

        # for timestep in range(self.number_increments): 
        #     print(f"-"*20, f"timestep : {timestep}", f"-"*20)

    def load_hourly_consumption(self):
        # Get the directory of the current script, which is under abm
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # Go up one level from abm to p2p_solar_abm, then into the data folder
        file_path = os.path.join(dir_path, '..', 'data', 'hourly_consumption.csv')

        # Ensure the path is normalized to resolve any .. or . correctly
        full_path = os.path.normpath(file_path)

        # Reading the file
        data = pd.read_csv(full_path)
        return data



