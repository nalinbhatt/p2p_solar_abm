from abm.household import Household
import json 
import pandas as pd
import os
import numpy as np 
import math 


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
        self.observe_daylight_savings = False # Hawaii doesn't observe daylight savings 
        self.begin_month_day = 244

        # Internal State Variables
        self.initialized = False
        self.current_minute = 660 #needs to be 0
        self.increment = 60
        self.current_increment = 12 #needs to be 1 
        self.number_increments = self.minutes_in_month // self.increment
        
        # Simulation Configuration
        self.storage_sim = 1
        self.forecasting_method = 0 #perfect forecasting 
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
        print(f"Minute: {self.current_minute}")
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
        total_houses = len(household_configs) #total households
        self.households = [] #list to store household objects

        #Household Energy Demand initialization
        demandLedger = np.zeros((total_houses, self.hours_in_month))
        demandLedgerMinutely = np.zeros((total_houses, self.hours_in_month * 60))

        hourly_cons_df = self.load_data_file("hourly_consumption")
        #Converts DataFrame column to Series
        hourly_demand_series = hourly_cons_df['hourly_consumption'].squeeze()  

        #Household/Prosumer Energy solar irradiance array
        minutely_monthly_prod_df = self.load_data_file("production_monthly_minutely")
        minutely_monthly_prod_series = minutely_monthly_prod_df.squeeze() 

        #solar energy production array 
        self.solar_energy_production_arr = self.adjustIrradiance(minutely_monthly_prod_series)

        #print(solar_energy_production_arr[0:1000])
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

            #we set their minutely production 
            #There are a lot of assumptions
            #for more details on this equation look at the jupyter notebook
            house_estimated_minutely_production = self.solar_energy_production_arr * 0.092903 * (household_obj.roof_area * 0.10) * 0.253 * 0.77
            household_obj.set_solar_production(house_estimated_minutely_production)
            household_obj.set_forecasted_solar_production() #set the solar forecast 
            

            #Lastly, add households to a household list
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
        print(f"-"*30, "Initializing", f"-"*30)

        
        self.initialize_households()
        print(f"-"*30, "Initialization Complete", f"-"*30)

        for timestep in range(self.number_increments): 
            
            self.exchangeNoStorage()
            print(f"-"*20, f"timestep : {timestep}", f"-"*20)

            return 

    
    def exchangeNoStorage(self):
        continuation_flag = True
        current_round = 0


        while continuation_flag:
            excess = np.zeros(self.number_houses)
            demand = np.zeros(self.number_houses)

            for i in range(self.number_houses):
                print(f"-"*5, f"Household: {i}",f"-"*5)

                household = self.households[i]

                if self.forecasting_method == 0:  # Perfect forecasting
                    # household.perfect_forecast = True
                    print(f"buyer History: {self.buyer_history[i][self.current_increment - 1][0]}")
                    demand[i] = max(household.forecast_demand_no_storage_simple() - self.buyer_history[i][self.current_increment - 1][0], 0)
                    excess[i] = max(household.forecast_excess_no_storage_simple() - self.seller_history[i][self.current_increment - 1][0], 0)
                elif self.forecasting_method == 1:  # Simple forecasting
                    demand[i] = max(household.forecast_demand_no_storage_simple() - self.buyer_history[i][self.current_increment - 1][0], 0)
                    excess[i] = max(household.forecast_excess_no_storage_simple() - self.seller_history[i][self.current_increment - 1][0], 0)
                elif self.forecasting_method == 2:  # Complex forecasting
                    demand[i] = max(household.forecast_demand_no_storage_complex() - self.buyer_history[i][self.current_increment - 1][0], 0)
                    excess[i] = max(household.forecast_excess_no_storage_complex() - self.seller_history[i][self.current_increment - 1][0], 0)

            print(f"demand : {demand}")
            print(f"excess : {excess}")
           
            # Boolean flag for zero demand
            zero_demand = np.all(demand <= 0)
            if zero_demand:
                continuation_flag = False

            # Boolean flag for zero excess
            zero_excess = np.all(excess <= 0)
            if zero_excess:
                print(f"zero excess shutting down now")
                continuation_flag = False

            buyer_count = np.sum(demand > 0)
            seller_count = np.sum(excess > 0)
            buyer_index = np.where(demand > 0)[0]
            seller_index = np.where(excess > 0)[0]

            # Order buyers by willingness to pay (WTP)
            buyers_ordered = sorted(buyer_index, key=lambda x: self.households[x].get_wtp(), reverse=True)

            # Order sellers by willingness to accept (WTA)
            sellers_ordered = sorted(seller_index, key=lambda x: self.households[x].get_wta())

            total_exchanges = min(len(buyers_ordered), len(sellers_ordered))

            print(f"buyers_ordered = {buyers_ordered}")
            print(f"sellers = {sellers_ordered}")
            print(f"total_exchanges = {total_exchanges}")
           
            # Boolean flag to check WTA and WTP of first paired traders
            if not buyers_ordered or not sellers_ordered or self.households[buyers_ordered[0]].get_wtp() < self.households[sellers_ordered[0]].get_wta():
                continuation_flag = False


            try:
                print(f"wtp arr = {self.households[buyers_ordered[0]].get_wtp()}")
                print(f"wta arr = {self.households[sellers_ordered[0]].get_wta()}")
            except: 
                print(f"buyers_ordered or sellers_ordered empty")
                print(f"continuation_flag = {continuation_flag}")
                

            print(f"-"*5, f"Exchange Time", f"-"*5)

            for i in range(total_exchanges):
                print(f"Match number : {i + 1}")
                seller_index2 = sellers_ordered[i]
                buyer_index2 = buyers_ordered[i]



                seller_wta = self.households[seller_index2].get_wta()
                buyer_wtp = self.households[buyer_index2].get_wtp()
                seller_cap = excess[seller_index2]
                buyer_need = demand[buyer_index2]
                
                # Exchange Amount in units of kWh
                exchange_amount = min(seller_cap, buyer_need) if seller_wta <= buyer_wtp else 0

                print(f"seller_index2 = {seller_index2}, buyer_index2 = {buyer_index2}")
                print(f"seller_wta = {seller_wta}, buyer_wtp = {buyer_wtp}")
                print(f"seller_cap = {seller_cap}, buyer_need = {buyer_need}")
                print(f"exchange_amount = {exchange_amount}, amount paid = {exchange_amount * buyer_wtp}")

                if exchange_amount > 0:
                    print(f"Trade Sucessful")
                    self.seller_history[seller_index2][self.current_increment - 1][0] += exchange_amount
                    self.seller_history[seller_index2][self.current_increment - 1][1] += buyer_wtp * exchange_amount
                    self.buyer_history[buyer_index2][self.current_increment - 1][0] += exchange_amount
                    self.buyer_history[buyer_index2][self.current_increment - 1][1] += buyer_wtp * exchange_amount

            current_round += 1

        for i in range(self.number_houses):
            self.households[i].fill_solar_prod_forecast_increment()


    def adjustIrradiance(self, irradianceArray):
        """ 
        Uses minutely irradiance to calculate the amount of solar energy produced 
        from a fixed-tilt solar panel. 

        Input: 
            irradianceArray (np arr): one dimensional minutely solar irradience 
                                     array of length equivalant to minutes in a
                                     month. 
        """

        declination = np.zeros(self.minutes_in_month)
        hourAngle = np.zeros(self.minutes_in_month)
        altitudeAngle = np.zeros(self.minutes_in_month)
        solarAzimuth = np.zeros(self.minutes_in_month)
        C = np.zeros(self.minutes_in_month)
        incidenceAngle = np.zeros(self.minutes_in_month)
        beamRad = np.zeros(self.minutes_in_month)
        diffuseRad = np.zeros(self.minutes_in_month)
        reflectedRad = np.zeros(self.minutes_in_month)
        collectorRad = np.zeros(self.minutes_in_month)

        for i in range(self.days_in_month):
            currentDeclination = 23.45 * math.sin(math.radians((360/365) * (self.begin_month_day + i)))
            minuteOfSolarNoon = self.solarNoon(self.begin_month_day + i)
            currentC = 0.095 + (0.04 * math.sin(math.radians((360/365) * (self.begin_month_day + i - 100))))

            for j in range(1440): #minutes in one day = 60*24 = 1440  
                currentMinute = (1440 * i) + j
                declination[currentMinute] = currentDeclination
                minutesFromSolarNoon = (minuteOfSolarNoon - j)
                hourAngle[currentMinute] = (minutesFromSolarNoon / 60.0) * 15.0
                altitudeAngle[currentMinute] = math.degrees(math.asin(math.cos(math.radians(self.latitude)) * 
                                            math.cos(math.radians(declination[currentMinute])) * 
                                            math.cos(math.radians(hourAngle[currentMinute])) + 
                                            (math.sin(math.radians(self.latitude)) * 
                                             math.sin(math.radians(declination[currentMinute])))))
                solarAzimuth[currentMinute] = math.degrees(math.asin((math.cos(math.radians(declination[currentMinute])) * 
                                          math.sin(math.radians(hourAngle[currentMinute])))/
                                          (math.cos(math.radians(altitudeAngle[currentMinute])))))
                incidenceAngle[currentMinute] = math.degrees(math.acos(math.cos(math.radians(altitudeAngle[currentMinute])) * 
                                           math.cos(math.radians(solarAzimuth[currentMinute])) * 
                                           math.sin(math.radians(self.latitude)) + 
                                           (math.sin(math.radians(altitudeAngle[currentMinute])) * 
                                            math.cos(math.radians(self.latitude)))))
                C[currentMinute] = currentC
                beamRad[currentMinute] = irradianceArray[currentMinute] * math.cos(math.radians(incidenceAngle[currentMinute]))
                diffuseRad[currentMinute] = irradianceArray[currentMinute] * currentC * ((1 + math.cos(math.radians(self.latitude))) / 2)
                reflectedRad[currentMinute] = irradianceArray[currentMinute] * 0.2 * (currentC + math.sin(math.radians(altitudeAngle[currentMinute]))) * ((1 - math.cos(math.radians(self.latitude))) / 2)
                collectorRad[currentMinute] = beamRad[currentMinute] + diffuseRad[currentMinute] + reflectedRad[currentMinute]

        return collectorRad

    def solarNoon(self, n):
        """ 
        Calculates the minute at which the solar noon occurs for a given day. 
        For instance, the day has 24*60 = 1440 minutes, and the solar noon can 
        occur at 12 pm or 720th minute of the day. Therefore the following code 
        would return 720: 

        Input: 
            n (int): nth day of the year, if the month is september then it 
                    ranges from 244 - 274 (30 days). 

        RETURN: 
            minute (int): minute at which the actual solar noon occurs. 
        
        """
        if self.observe_daylight_savings and (69 <= n <= 307):
            self.day_light_savings = True
        else:
            self.day_light_savings = False

        longitudeCorrection = 4.0 * (self.local_time_meridian - self.longitude)  # Units of minutes
        Bdegrees = (360.0/364.0) * (n - 81)
        Bradians = math.radians(Bdegrees)
        E = (9.87 * math.sin(2 * Bradians)) - (7.53 * math.cos(Bradians)) - (1.5 * math.sin(Bradians))  # Units of minutes
        minutesFromClockNoon = -longitudeCorrection - E
        minutesFromClockNoonInt = int(round(minutesFromClockNoon))
        
        if self.day_light_savings:
            return (13 * 60) + minutesFromClockNoonInt
        else:
            return (12 * 60) + minutesFromClockNoonInt
        

    def load_data_file(self, filename):
        """ 
        loads the .csv datafile from under the data folder. Note, 
        this method doesn't require an extension specification, the file 
        is assumed to be a .csv so just the filename suffices 

        INPUT: 
            filename (str): the str filename of the data file without the 
                            extension
        
        RETURN: 
            data (pd dataframe): dataframe object read in from th csv
        """
        # Get the directory of the current script, which is under abm
        dir_path = os.path.dirname(os.path.realpath(__file__))

        # Go up one level from abm to p2p_solar_abm, then into the data folder
        file_path = os.path.join(dir_path, '..', 'data', f'{filename}.csv')

        # Ensure the path is normalized to resolve any .. or . correctly
        full_path = os.path.normpath(file_path)

        # Reading the file
        data = pd.read_csv(full_path)
        return data


