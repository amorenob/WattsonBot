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
DC_TO_AC_DERATE = 0.995
INSTALLATION_LIFE_SPAN = 25
COST_INCREASE_FACTOR = 1.0318
DISCOUNT_RATE = 1.0499
INCENTIVES = 0
AVG_INSTALLED_COST_PER_KW = 6480000
AVG_INSTALLATION_FIXED_COST = 2453000