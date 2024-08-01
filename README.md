# Testing optimal AMM liquidity in P2P Energy Markets: A bold endeavor
Nalin Bhatt 

This is an Agent-based modeling project that is based on the Monroe et. al (2023) model. We extend the original model by adding an Automated Market Makers (AMMs) and monitoring effects on amounts of solar electricity sold within the market. 

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/nalinbhatt/p2p_solar_abm.git
cd p2p_solar_abm
```

# Create the environment
```bash 
conda create --name myenv python=3.11.5
```

# Activate the environment
```bash
conda activate myenv
```

# install requirements

```bash 
pip install -r requirements.txt
```



# Running a single config file 

```bash
python single_run.py
```

# Running batch simulations 
```bash
python batch_run.py
```



# Repository Structure
```
LICENSE  
├── **Readme.md**: main folder that contains model code   
├── **Solar Market - United States Simulations.zip** : Original simulation java code from which this simulation is adapted  
├── **abm**: Main folder that contains all agent-based model code  
│   ├── **amm.py** : contains the AMM class  
│   ├── **household.py**: contains the Household class  
│   └── **model.py** : contains the Market class that has all the model running code  
├── **analysis_notbook.ipynb**: contains the code for the different graphs produced   
├── **batch_run.py**: contains python code to run all combinations of the configs files present in ```batch_run.json```  
├── **configurations**: folder that contains the simulation configs  
│   ├── **batch_run.json**: contains all the json files that have all parameter configurations for our batch_run  
│   ├── **household_params**: contains the household profile code that we use to initialize all the households with  
│   │   ├── prosumer1.json: the number corresponds with number of households that have solar   
│   │   ├── prosumer10.json  
│   │   ├── prosumer11.json  
│   │   ├── prosumer12.json  
│   │   ├── prosumer2.json  
│   │   ├── prosumer3.json  
│   │   ├── prosumer4.json  
│   │   ├── prosumer5.json  
│   │   ├── prosumer6.json  
│   │   ├── prosumer7.json  
│   │   ├── prosumer8.json  
│   │   └── prosumer9.json  
│   └── **single_run.json**: If you want to evaluate results from a single run, this is the file called by    
                            single_runner.py   
├── **cons_prod_data**: contains the external data included in the model  
│   ├──**hourly_consumption.csv**: contains hourly consumption data in W/h   
│   └── **production_monthly_minutely.csv**: contains minutely production information in W/h  
├── **generate_batchrun_config.ipynb**: notebook used to create batch_run.json  
├── **model_design.ipynb**: contains all the math regarding solar conversions, amm math, equilibrium price math and much more  
├── **requirements.txt**: all the requirements necessary to run the code  
├── **simulation_logs**: incomplete, pet project to have separate folder that the simulation logs to instead of using print statements  
├── simulation_output  
│   └── **aggregate_sim_data.csv** : ALl the aggregate simulation data gets logged to the file after batch runs, individual time-step data is being tracked in the model but not currently logged   
└── **single_run.py**: contains code to run a single_run.json   
```

