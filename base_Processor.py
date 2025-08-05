import simpy
from config_SimPy import *

class Worker:
    """
    Worker class to represent a worker in the manufacturing process
    One type of processor in the simulation

    Attributes:
        type_processor (str): Type of processor (Worker)
        id_worker (int): Worker ID
        name_worker (str): Worker name
        available_status (bool): Worker availability status
        working_item (item): item currently being processed
        processing_time (int): Time taken to process a item
        busy_time (int): Total time spent processing items
        last_status_change (int): Time of last status change
    """

    def __init__(self, id_worker, name_worker, processing_time):
        self.type_processor = "Worker"
        self.id_worker = id_worker
        self.name_worker = name_worker
        self.available_status = True
        self.working_item = None
        self.processing_time = processing_time
        self.busy_time = 0
        self.last_status_change = 0


class Machine:
    """
    Machine class to represent a machine in the manufacturing process
    One type of processor in the simulation

    Attributes:
        type_processor (str): Type of processor (Machine)
        id_machine (int): Machine ID
        name_process (str): Process name
        name_machine (str): Machine name
        available_status (bool): Machine availability status
        list_working_items (list): List of items currently being processed
        capacity_items (int): Maximum number of items that can be processed simultaneously
        processing_time (int): Time taken to process a item
        busy_time (int): Total time spent processing items
        last_status_change (int): Time of last status change
        allows_item_addition_during_processing (bool): Flag to allow item addition during processing
    """

    def __init__(self, id_machine, name_process, name_machine, processing_time, capacity_items=1):
        self.type_processor = "Machine"
        self.id_machine = id_machine
        self.name_process = name_process
        self.name_machine = name_machine
        self.available_status = True
        self.list_working_items = []
        self.capacity_items = capacity_items
        self.processing_time = processing_time
        self.busy_time = 0
        self.last_status_change = 0
        self.allows_item_addition_during_processing = False

class AMR:
    """
    Autonomous Mobile Robot
    
    Attributes:
    - type_processor: "AMR"
    - id_amr: Unique identifier for the AMR
    - name_amr: AMR’s display name
    - processing_time: Time required to transport or process one item
    - capacity_items: Maximum number of items that can be carried at once
    - allows_item_addition_during_processing: Whether the AMR can pick up additional items while moving
    - workload (list): List of items currently assigned to this AMR for transport
    """
    
    def __init__(self, id_amr, name_amr, processing_time, capacity_items=1):
        self.type_processor = "AMR"
        self.id_amr = id_amr
        self.name_amr = name_amr
        self.processing_time = processing_time
        self.capacity_items = capacity_items
        # Whether new items can be added to the AMR’s load during transport
        self.allows_item_addition_during_processing = True
        # List to track items currently assigned to this AMR
        self.workload = []       
        
class ProcessorResource(simpy.Resource):
    """
    Integrated processor (Machine, Amr, Worker) resource management class that inherits SimPy Resource
    
    Args:
        processor_type (str): Type of processor (Machine/Worker)
        id (int): Processor ID
        name (str): Processor name
        allows_item_addition_during_processing (bool): Flag to allow item addition during processing
        current_items (list): List of items currently being processed (Machines)
        current_item (item): item currently being processed (Worker)
        processing_time (int): Time taken to process a item
        processing_started (bool): Flag to prevent further resource allocation after processing starts
    """
    
    def __init__(self, env, processor):
        # Check processor type and set properties
        self.processor_type = getattr(processor, 'type_processor', 'Unknown')

        # Set capacity - Machine uses capacity_items, Worker always 1
        if self.processor_type == "Machine":
            capacity = getattr(processor, 'capacity_items', 1)
            self.id = getattr(processor, 'id_machine', 0)
            self.name = getattr(processor, 'name_machine', 'Machine')
            # Flag for allowing item addition during processing
            self.allows_item_addition_during_processing = getattr(
                processor, 'allows_item_addition_during_processing', True)
            # Current items being processed
            self.current_items = []
        elif self.processor_type == "Worker":
            capacity = 1  # Worker always processes one item at a time
            self.id = getattr(processor, 'id_worker', 0)
            self.name = getattr(processor, 'name_worker', 'Worker')
            # Worker never allows item addition during processing
            self.allows_item_addition_during_processing = False
            # Current item being processed
            self.current_item = None
            self.current_items = []  # Added for consistency
        elif self.processor_type == "AMR":
            capacity = processor.capacity_items
            self.id = processor.id_amr
            self.name = processor.name_amr
            # AMR never allows item addition during transporting
            self.allows_item_addition_during_processing = False
            # Current item being transported
            self.current_items = []

        # Initialize Resource
        super().__init__(env, capacity=capacity)

        self.processor = processor
        self.processing_time = getattr(processor, 'processing_time', 10)

        # Flag to prevent further resource allocation after processing starts
        self.processing_started = False

    def request(self, *args, **kwargs):
        """
        Override resource request - Check if addition during processing is allowed
        """
        # If already processing and addition not allowed, reject request
        if self.processing_started and not self.allows_item_addition_during_processing:
            # Return a dummy event that mimics SimPy request but waits indefinitely
            dummy_event = self._env.event()
            dummy_event.callbacks.append(
                lambda _: None)  # Add callback to set to infinite wait state
            return dummy_event

        # Set flag when item is first assigned to resource
        if not self.processing_started and self.count == 0:
            self.processing_started = True

        # Process basic request
        return super().request(*args, **kwargs)

    def release(self, request):
        """
        Override resource release - Handle item completion
        """
        result = super().release(request)

        # Reset processing flag when all items are complete
        if self.count == 0:
            self.processing_started = False
            # For Machine and AMR, clear the list of current items
            if self.processor_type in ("Machine", "AMR"):
                self.current_items = []
            # For Worker, clear its single current item and the list
            else:  # Worker
                self.current_item = None
                self.current_items = []

        return result
    
    @property
    def is_available(self):
        """Check if processor is available"""
        # Not available if processing and additions not allowed
        if self.processing_started and not self.allows_item_addition_during_processing:
            return False

        # Available if capacity has room
        return self.count < self.capacity  # Use count attribute instead of count()

    def start_item(self, item):
        """Process item start"""
        if self.processor_type in ("Machine", "AMR"):
            # Add item to Machine or AMR
            self.current_items.append(item)
            if self.processor_type == "AMR":
                # Also record on the AMR object
                self.processor.workload.append(item)
        else:  # Worker
            # Set Worker's current item
            self.current_item = item
            self.current_items = [item]  # Add to list for consistency

        # Set workstation info in item
        if self.processor_type == "Machine":
            item.workstation["Machine"] = self.id
        elif self.processor_type == "AMR":
            item.workstation["AMR"] = self.id
        else:  # Worker
            item.workstation["Worker"] = self.id

    def get_items(self):
        """Return list of currently processing or transporting items"""
        if self.processor_type in ("Machine", "AMR"):
            return self.current_items
        else:  # Worker
            return [self.current_item] if self.current_item else []

    def finish_items(self):
        """Process item completion"""
        items = self.get_items()

        if self.processor_type in ("Machine", "AMR"):
            self.current_items = []
            if self.processor_type == "AMR":
                # Clear the AMR's own workload
                self.processor.workload = []
        else:  # Worker
            self.current_item = None
            self.current_items = []

        return items
