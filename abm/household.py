from scipy.stats import norm
import numpy as np


class Household:
    def __init__(self, index, has_pv, floor_area, wta, wtp):
        self.index = index # index
        self.has_pv = has_pv # has solar or not 
        self.floor_area = floor_area # floor area 
        self.wta = wta  # willingness to accept, reservation price for selling
        self.wtp = wtp # willingness to pay, reservation price for buying
        self.roof_area = self.floor_area * 1.12
        self.days_month = 31
        self.minutes_month = self.days_month * 24 * 60
        self.increment = 60
        self.number_increments = self.minutes_month // self.increment
        self.increments_per_hour = 60 // self.increment
        self.increments_per_day = 1440 // self.increment
        self.start_charge = 9
        self.stop_charge = 14
        self.start_charge_inc = self.increments_per_hour * self.start_charge
        self.stop_charge_inc = self.increments_per_hour * self.stop_charge
        self.start_discharge = 17
        self.stop_discharge = 22
        self.start_discharge_inc = self.increments_per_hour * self.start_discharge
        self.stop_discharge_inc = self.increments_per_hour * self.stop_discharge
        self.cell_efficiency = 0.253
        self.irradiation = 0.0929
        self.solar_proportion = 0.10
        self.price_kw = 3090
        self.interest_rate = 0.07
        self.minimum_charge = 4.05
        self.maximum_charge = 13.5
        self.electricity_use = np.zeros(self.minutes_month)
        self.solar_prod = np.zeros(self.minutes_month)
        self.solar_prod_forecast = np.zeros(self.minutes_month)
        self.solar_prod_forecast_increment = np.zeros(self.number_increments)
        self.demand = np.zeros(self.number_increments)
        self.demand_after_storage_discharge = np.zeros(self.number_increments)
        self.demand_after_solar_storage = np.zeros(self.number_increments)
        self.production = np.zeros(self.number_increments)
        self.production_for_demand = np.zeros(self.number_increments)
        self.production_after_demand = np.zeros(self.number_increments)
        self.production_for_market = np.zeros(self.number_increments)
        self.production_remaining_after_market = np.zeros(self.number_increments)
        self.production_for_storage = np.zeros(self.number_increments)
        self.production_for_utility = np.zeros(self.number_increments)
        self.storage = np.zeros(self.number_increments)
        self.storage_initially_discharged = np.zeros(self.number_increments)
        self.storage_after_initial_discharge = np.zeros(self.number_increments)
        self.storage_discharge_market = np.zeros(self.number_increments)
        self.initialize_elec_attributes()

    def initialize_elec_attributes(self):
        self.calc_peak_power()
        self.calc_investment_cost()
        self.calc_annual_prod()
        self.calc_prod_20()

    
    def calc_peak_power(self):
        self.peak_power = self.irradiation * self.solar_proportion * self.roof_area * self.cell_efficiency

    def calc_investment_cost(self):
        self.investment_costs = self.peak_power * self.price_kw

    def calc_annual_prod(self):
        self.expected_production = self.peak_power * 8760 * 0.23

    def calc_prod_20(self):
        self.expected_production_20 = self.expected_production * 20

    def set_electricity_use(self, elec_use):
        self.electricity_use = elec_use
        
        print(self.electricity_use)

    def get_electricity_use(self, minute):
        return self.electricity_use[minute]

    def set_solar_production(self, production):
        self.solar_prod = production

    def get_solar_production(self, minute):
        return self.solar_prod[minute]

    def set_forecasted_solar_production(self):
        normal_dist = norm(0, 0.30)
        forecast_multiplier = normal_dist.rvs(size=self.minutes_month) + 1
        self.solar_prod_forecast = self.solar_prod * forecast_multiplier

    def fill_solar_prod_forecast_increment(self):
        for i in range(self.number_increments):
            start_minute = i * self.increment
            end_minute = start_minute + self.increment
            if self.has_pv:
                self.solar_prod_forecast_increment[i] = np.sum(self.solar_prod_forecast[start_minute:end_minute]) / 1000 / 60
            else:
                self.solar_prod_forecast_increment[i] = 0

    def __str__(self):
        return (f"Household(Index: {self.index}, Has PV: {'Yes' if self.has_pv else 'No'}, "
                f"Type: {'Prosumer' if self.has_pv else 'Consumer'},"
                f"Floor Area: {self.floor_area} sqft, "
                f"Willingness to Accept: ${self.wta:.2f}, "
                f"Willingness to Pay: ${self.wtp:.2f})")
    



    

        

