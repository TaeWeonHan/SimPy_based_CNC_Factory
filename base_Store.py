import simpy
from config_SimPy import *

class ItemStore(simpy.Store):
    """
    Item queue management class that inherits Simpy Store
    
    Args:
        env (simpy.Environment): Simulation environment
        name (str): Name of the ItemStore
        queue_length_history (list): Queue length
    """
    
    def __init__(self, env, name="ItemStore"):
        super().__init__(env)
        self.name = name
        self.queue_length_history = [] # Track queue length history
        
    def put(self, item):
        """Add item to Store (override)"""
        result = super().put(item)
        # Record queue length
        self.queue_length_history.append((self._env.now, len(self.items)))
        return result
    
    def rework_put(self, item):
        """
        Add a reprocessed item to the store according to the FRONT/MIDDLE/BACK policy:
        * FRONT: place after all existing reprocessed items (idx = number of existing reprocess items)
        * MIDDLE: insert at floor(len/2) plus offset for same-timestamp reprocess items with lower IDs
        * BACK: append to the end of the queue
        """
        # 1) Perform the standard put to append the item and get the event result
        result = super().put(item)

        # 2) Remove the newly appended item from the end of the internal list
        items = self.items  # internal Python list of stored items
        new_item = items.pop(-1)

        # 3) Determine insertion index based on the configured policy
        pos = POLICY_REPROC_INSERT_POSITION.upper()
        if pos == "FRONT":
            # Count existing reprocessed items for front insertion
            idx = sum(1 for j in items if getattr(j, "is_reprocess", False))

        elif pos == "MIDDLE":
            # Base index at the middle of the current queue
            base_index = len(items) // 2
            # Offset by the number of same-timestamp reprocessed items with lower IDs
            offset = sum(
                1
                for j in items
                if getattr(j, "is_reprocess", False)
                and getattr(j, "time_waiting_start", None) == self._env.now
                and j.id_item < new_item.id_item
            )
            idx = base_index + offset

        else:  # BACK
            # Simply append to the end
            idx = len(items)

        # 4) Insert the item at the calculated index
        items.insert(idx, new_item)

        # 5) Record the new queue length
        self.queue_length_history.append((self._env.now, len(items)))

        return result
    
    def get(self):
        """Get item from queue (override)"""
        result = super().get()
        # Record queue length when getting result

        # Use event chain instead of callback
        def process_get(env, result):
            item = yield result
            self.queue_length_history.append((self._env.now, len(self.items)))
            return item

        return self._env.process(process_get(self._env, result))
    
    @property
    def is_empty(self):
        """Check if queue is empty"""
        return len(self.items) == 0

    @property
    def size(self):
        """Current queue size"""
        return len(self.items)
    
class ItemSupplier(simpy.Store):
    """
    Raw material supplier implemented as a SimPy Store.

    Attributes:
        env (simpy.Environment): simulation env
        supply_type (str): "LOT" or "PALLET"
        supplier_id (int): resource spplier inherence id
        capacity (int): initial inventory (read by config)
    """

    def __init__(self, env, supply_type: str, supplier_id: int):
        super().__init__(env)
        self.env = env
        self.supply_type = supply_type.upper()
        self.supplier_id = supplier_id

        # Set initial inventory according to supply_type
        if self.supply_type == "LOT":
            self.capacity = LOT_INVEN_LEVEL
        elif self.supply_type == "PALLET":
            self.capacity = PALLET_INVEN_LEVEL
        else:
            raise ValueError(f"Invalid supply_type: {supply_type!r}")

        # Insert initial inventory in the form of a token in the Store internal list (items)
        # (In the current simulation, tokens are expressed with 'None' or a simple dict.)
        for _ in range(self.capacity):
            # 예시: 단순 None 토큰
            self.items.append(None)

        # (선택) 생성 시 로그 출력
        # print(f"[{self.env.now}] Supplier {self.supply_type}-{self.supplier_id} initialized with {self.capacity} units")

    def get_material(self):
        """
        Used to import only one raw material.
        ex: yield supplier.get_material()
        """
        return self.get()

    def get_bulk(self, amount: int):
        """
       Used to take out multiple raw materials at once.
        ex: yield supplier.get_bulk(10)
        """
        # Collect each get() event and return it as an AllOf event
        events = [self.get() for _ in range(amount)]
        return simpy.events.AllOf(self.env, events)