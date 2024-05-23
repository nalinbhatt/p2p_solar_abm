from abm.model import Market
import json 



if __name__ == "__main__":

    # Loading the simulation configuration information 
    config_dict = {} 
    file_path = "configurations/batch_run.json" 

    with open(file_path, 'r') as config_file:
        config_dict_list = json.load(config_file)
    
    #There are a list of configurations that we are running 
    for config_dict in config_dict_list:
        prosumer_count = config_dict["prosumer_count"]
        #Imports the relevant household param json file from configurations/household_params/ folder
        #adds that to the config_dict and passes the rest to the Market class
        with open(f"configurations/household_params/prosumer{prosumer_count}.json", 'r') as config_file:
            household_params = json.load(config_file)
        
        config_dict["household_params"] = household_params["household_params"]
        num_runs = config_dict["n_runs"] #number of times we run the same configuration
        
        #for multirun simulation, 
        for run_number in range(1, num_runs + 1): 
            abm_model = Market(config_dict,run_number)
            abm_model.run_simulation()