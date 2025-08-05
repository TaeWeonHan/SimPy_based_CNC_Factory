import random
from config_SimPy import *
from base_Process import Process
from specialized_Processor import Mach_CNC, Mach_AMR1, Mach_AMR2, Worker_Inspect

class Proc_Cutting(Process):
    """
    CNC Process
    inherits from Process class
    """
    
    def __init__(self, env, logger=None):
        super().__init__("Proc_Cutting", env, logger)
        
        # Initialize CNC machines
        for i in range(NUM_MACHINES_CNC):
            self.register_processor(Mach_CNC(i+1))
    
    def apply_special_processing(self, processor, items):
        """CNC special processing - possibility of defects"""
        for item in items:
            if random.random() < DEFECT_RATE_PROC_BUILD:
                item.is_defect = True
            else:
                item.is_defect = False
        return True
    
class Proc_Inspect(Process):
    """
    Inspection Process
    inherits from Process class
    """
    
    def __init__(self, env, manager=None, logger=None):
        super().__init__("Proc_Inspect", env, logger)

        self.manager = manager

        # Initialize inspection workers
        for i in range(NUM_WORKERS_IN_INSPECT):
            self.register_processor(Worker_Inspect(i+1))

    def apply_special_processing(self, processor, items):
        """Inspection process special processing - defect identification"""
        if isinstance(processor, Worker_Inspect):
            
            # Inspect each item
            for item in items:
                # Identify defects
                if item.is_defect:
                    
                    if self.logger:
                        self.logger.log_event(
                            "Inspection", f"Found defective items in order {item.id_order}"
                        )
                    self.manager.allocate_item_for_proc_defect(item)
                else:
                    # Mark normal items as completed
                    item.is_completed = True
        # Return True to indicate processing was done
        return True

class Proc_Amr_STC(Process):
    """
    Transport from Supplier → CNC
    inherits from Process class
    """
    def __init__(self, env, logger=None):
        super().__init__("Proc_AMR_STC", env, logger)
        # STC 전용 AMR 등록
        for i in range(NUM_STC_MACHINES_AMR):
            self.register_processor(Mach_AMR1(i+1))


class Proc_Amr_CTI(Process):
    """
    Transport from CNC → Inspect
    inherits from Process class
    """
    def __init__(self, env, logger=None):
        super().__init__("Proc_AMR_CTI", env, logger)
        # CTI 전용 AMR 등록
        for j in range(NUM_CTI_MACHINES_AMR):
            self.register_processor(Mach_AMR2(j+1))