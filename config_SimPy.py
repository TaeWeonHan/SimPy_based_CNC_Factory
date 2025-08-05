import random

""" Simulation settings """

# Simulation time settings
SIM_TIME = 7 * 24 * 60 # (unit: minutes)

# Logging and visualization settings
EVENT_LOGGING = True # Event logging enable/disable flag
DETAILED_STATS_ENABLED = True # Detailed statistics display flag

# Visualization flags
GANTT_CHART_ENABLED = True  # Gantt chart visualization enable/disable flag
VIS_STAT_ENABLED = False  # Statistical graphs visualization enable/disable flag
SHOW_GANTT_DEBUG = False  # 기본값은 False로 설정

""" Process setting """

# Process time setting
PROC_TIME_CUTTING = 180 # Process time for build (unit: minutes)
PROC_TIME_INSPECT = 0 # Process time for inspect per item (unit: minutes)
STC_PROC_TIME_TRANSIT = 3 # Time for AMR to move the product Supplier to CNC
CTI_PROC_TIME_TRANSIT = 3 # Time for AMR to move the product CNC to Inspector

# Resource settings
NUM_MACHINES_CNC = 2 # Number of CNC machines
NUM_CTI_MACHINES_AMR = 2 # Number of AMR machines (This amr is transporting item CNC to Inspector.)
NUM_STC_MACHINES_AMR = 2 # Number of AMR machines (This amr is transporting item Item Supplier to CNC.)
NUM_WORKERS_IN_INSPECT = 5 # Number of workers in inspection process
CAPACICTY_MACHINE_CUTTING = 1 # Item capacity for cutting
CAPACITY_MACHINE_AMR = 6 # Item capacity for transporting

# Process settings
DEFECT_RATE_PROC_BUILD = 0  # 5% defect rate in build process
# Item priority settings ("FRONT", "MIDDLE", "BACK")
POLICY_REPROC_INSERT_POSITION = "FRONT"

""" Supplier settings """
NUM_SUPPLIER_PALLET = 1
NUM_SUPPLIER_LOT = 1

LOT_INVEN_LEVEL = 100000000 # Number of raw materials of lot entering the CNC machine
PALLET_INVEN_LEVEL = 10000000 # Number of raw materials of pallet entering the CNC machine

# Decision supply place 
def SUPPLY_TYPE_DECISION():
    KEY_NUM = random.randint(0, 1)
    if KEY_NUM == 0:
        return "LOT"
    else:
        return "PALLET"
    
""" Customer settings """

# Number of items per order
def NUM_ITEMS_PER_ORDER(): return random.randint(
    2, 2)

# Customer settings
CUST_ORDER_CYCLE = 3 * 24 * 60  # Customer order cycle (1 week in minutes)