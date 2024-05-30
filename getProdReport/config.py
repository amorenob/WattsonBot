# Panels area
import os 

PANELS_AREA = {
    400: 2.0,
}

TEMP_DIR = '/tmp'
NREL_API_KEY = os.environ['NREL_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
API2PDF_API_KEY = os.environ['API2PDF_API_KEY']


# Solar financials
DC_TO_AC_DERATE = 0.995 # Is the ratio of the AC power output of the inverter to the DC power input of the inverter
INSTALLATION_LIFE_SPAN = 25 # Life span of the installation in years
COST_INCREASE_FACTOR = 1.0318 # The factor by which the cost of electricity increases each year
DISCOUNT_RATE = 1.0499 # The rate at which future costs are discounted
INCENTIVES = 0 # Local incentives for solar installations
AVG_INSTALLED_COST_PER_KW = 6480000 # Average cost of installing a solar system per kW
AVG_INSTALLATION_FIXED_COST = 2453000 # Average fixed cost of installing a solar system