# Testing optimal AMM liquidity in P2P Energy Markets: A bold endeavor
Nalin Bhatt 

This is an Agent-based modeling project that is based on the Monroe et. al (2023) model. We extend the original model by replacing the exchange mechanism with an Automated Market Makers (AMMs) and monitoring effects on amounts of solar electricity sold within the market. 


# Project Name

## Overview

Brief description of the project.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
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





├── LICENSE
├── Readme.md
├── abm
│   |
│   ├── exchange.py 
│   ├── household.py
│   └── model.py
├── analysis_notbook.ipynb
├── batch_run.py
├── configurations
│   ├── batch_run.json
│   ├── household_params
│   │   ├── prosumer1.json
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
│   ├── single_run.json
│   └── single_run_scenario1.json
├── cons_prod_data
│   ├── hourly_consumption.csv
│   └── production_monthly_minutely.csv
├── model_design.ipynb
├── requirements.txt
├── sequence_diagrams
│   ├── hourly_timestep.txt
│   └── overall_model.txt
└── single_run.py