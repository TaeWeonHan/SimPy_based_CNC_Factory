from config_SimPy import *
from specialized_Process import *
from base_Customer import OrderReceiver
from base_Store import *
import math

class Manager(OrderReceiver):
    """
    Manager class to control the manufacturing processes and track orders

    Attributes:
        env (simpy.Environment): Simulation environment
        logger (Logger): Logger object for logging events
        next_job_id (int): Next job ID counter
        completed_orders (list): List of completed orders
        processed_orders (list): List of processed orders
        suppliers_lot (list[ItemSupplier]): LOT-type item suppliers
        suppliers_pallet (list[ItemSupplier]): PALLET-type item suppliers
        suppliers (list[ItemSupplier]): All item suppliers combined
    """
    
    def __init__(self, env, logger=None):
        self.env = env
        self.logger = logger
        
        # Tracking completed items and orders
        self.completed_orders = []
        
        # Tracking processed items and orders
        self.processed_orders = []
        
        # Tracking processed items
        self.processed_items = []
        
        # —————————— Create Item Suppliers ——————————
        # 1) Create LOT-type item suppliers
        self.suppliers_lot = [
            ItemSupplier(self.env, "LOT", idx + 1)
            for idx in range(NUM_SUPPLIER_LOT)
        ]

        # 2) Create PALLET-type item suppliers
        self.suppliers_pallet = [
            ItemSupplier(self.env, "PALLET", idx + 1)
            for idx in range(NUM_SUPPLIER_PALLET)
        ]

        # 3) Combine all suppliers into one list for easy access
        self.suppliers = self.suppliers_lot + self.suppliers_pallet

        # When calling setup_processes, the manager (self) itself is also passed as an argument
        self.setup_processes(manager=self)
        
    def setup_processes(self, manager=None):
        """ Create and connect all manufacturing processes """
        # Create processes
        
        # 1) Supply->CNC Transport
        self.proc_transport_stc = Proc_Amr_STC(self.env, self.logger)
        
        # 2) CNC manufacturing
        self.proc_cutting = Proc_Cutting(self.env, self.logger)
        
        # 3) CNC -> Inspection Transport
        self.proc_transport_cti = Proc_Amr_CTI(self.env, self.logger)
        
        # 4) Inspection
        self.proc_inspect = Proc_Inspect(self.env, manager, self.logger)
        
        # Connect processes
        self.proc_transport_stc.connect_to_next_process(self.proc_cutting)
        self.proc_cutting.connect_to_next_process(self.proc_transport_cti)
        self.proc_transport_cti.connect_to_next_process(self.proc_inspect)
        
        if self.logger:
            self.logger.log_event(
                "Manager", "Manufacturing processes created and connected: AMR → Cutting → AMR → Inspect")
            
    def receive_order(self, order):
        """Process incoming order from Customer"""
        if self.logger:
            self.logger.log_event(
                "Order", f"Received Order {order.id_order} for Customer {order.id_customer} with {order.num_items} items")

        # Mark order start time and record number of items and total items
        order.time_start = self.env.now

        # Add items to processed list
        self.processed_items += order.list_items

        # Add order to processed orders list
        self.processed_orders.append(order)

        # Convert order to jobs based on policy
        self.allocate_items_for_proc_transport_stc(order)

        return order
    
    def allocate_items_for_proc_transport_stc(self, order):
        "Allocate items in CNC queue"
        for item in order.list_items:
            self.proc_transport_stc.add_to_queue(item)
            if self.logger:
                self.logger.log_event(
                    "Manager", f"Send item {item.id_item} of order {item.id_order} → STC_AMR"
                )
                
    def allocate_item_for_proc_defect(self, item):
        """Re-allocate defective item in CNC queue"""
        item.is_reprocess = True
        
        if self.logger:
            self.logger.log_event(
                "Manager",
                f"Re-allocating defective item {item.id_item} of order {item.id_order} back to Proc_Cutting"
            )
        # 다시 Cutting 큐에 넣기
        self.proc_cutting.add_to_queue(item)        
    def get_processes(self):
        """Return processes as a dictionary for statistics collection"""
        return {
            'cutting': self.proc_cutting,
            'inspect': self.proc_inspect
        }
        
    def collect_statistics(self):
        """Collect basic statistic from processes"""
        stats = {}
        
        # Completed jobs per process
        stats['cutting_completed'] = len(self.proc_cutting.completed_orders)
        stats['inspect_completed'] = len(self.proc_inspect.completed_orders)

        # Queue sizes
        stats['build_queue'] = self.proc_build.items_store.size
        stats['inspect_queue'] = self.proc_inspect.items_store.size

        # Defective items
        stats['defective_items'] = len(self.proc_inspect.defective_items)

        return stats