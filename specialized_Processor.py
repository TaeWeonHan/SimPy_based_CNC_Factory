from base_Processor import Worker, Machine, AMR
from config_SimPy import *

class Worker_Inspect(Worker):
    def __init__(self, id_worker):
        super().__init__(id_worker, f"Inspector_{id_worker}", PROC_TIME_INSPECT)
        
class Mach_CNC(Machine):
    def __init__(self, id_machine):
        super().__init__(id_machine, "Proc_CNC", f"CNC_{id_machine}", PROC_TIME_CUTTING, CAPACICTY_MACHINE_CUTTING)

class Mach_AMR1(AMR):
    def __init__(self, id_amr):
        super().__init__(id_amr, f"STC_AMR_LOT{id_amr}", STC_PROC_TIME_TRANSIT, CAPACITY_MACHINE_AMR)
             
class Mach_AMR2(AMR):
    def __init__(self, id_amr):
        super().__init__(id_amr, f"CTI_AMR_{id_amr}", CTI_PROC_TIME_TRANSIT, CAPACITY_MACHINE_AMR)