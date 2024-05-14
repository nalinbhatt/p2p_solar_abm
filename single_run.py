from abm.model import Market
from abm.consumer_agent import ConsumerAgent
from abm.prosumer_agent import ProsumerAgent
import json 



if __name__ == "__main__":

    config_dict = {} #
    with open("configurations/single_run.json", 'r') as config_file:
        config_dict = json.load(config_file)
        
    abm_model = Market(config_dict) #create
    abm_model.run_simulation()
    

