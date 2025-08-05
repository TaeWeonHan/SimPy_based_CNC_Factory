from base_Store import ItemStore
from base_Processor import ProcessorResource

class Process:
    """
    Base manufacturing process class for SimPy simulation
    
    Atrributes:
        name_process (str): Process identifier
        env (simpy.Environment): Simulation environment
        logger (Logger): Event logger
        list_processors (list): List of processors (Machines, Amr, Workers)
        item_store (ItemStore): Item queue management
        processor_resources (dict): Processor resources (Machine, Amr, Worker)
        completed_items (list): List of completed items
        next_process (Process): Next process in the flow
        resource_trigger (simpy.Event): Resource trigger event
        item_added_trigger (simpy.Event): item added trigger event
        process (simpy.Process): Main process execution    
    """
    
    def __init__(self, name_process, env, logger=None):
        self.name_process = name_process
        self.env = env
        self.logger = logger
        self.list_processors = [] # Processor list
        
        # Implement queue with ItemStore (Inherits SimPy Store)
        self.item_store = ItemStore(env, f"{name_process}_ItemStore")
        
        # Processor resource management
        self.processor_resources = {} # {processor_id: ProcessorResource}
        
        # Track completed items
        self.completed_items = []
        
        # Next process
        self.next_process = None
        
        # Add new events
        self.resource_trigger = env.event()
        self.item_added_trigger = env.event()
        
        # Start simulation process
        self.process = env.process(self.run())
        
        # if self.logger:
        #     self.logger.log_event(
        #         "Process", f"Process {self.name_process} created")

    def connect_to_next_process(self, next_process):
        """Connect directly to next process. Used for process initialization."""
        self.next_process = next_process
        # if self.logger:
        #     self.logger.log_event(
        #         "Process", f"Process {self.name_process} connected to {next_process.name_process}")
        
    def register_processor(self, processor):
        """Register processor (Machine or Amr or Worker). Used for process initialization."""
        # Add to processor list
        self.list_processors.append(processor)

        # Create ProcessorResource (integrated resource management)
        processor_resource = ProcessorResource(self.env, processor)

        # Determine id based on processor type
        if processor.type_processor == "Machine":
            processor_id = f"Machine_{processor.id_machine}"
        elif processor.type_processor == "AMR":
            processor_id = f"AMR_{processor.id_amr}"
        else:  # Worker
            processor_id = f"Worker_{processor.id_worker}"

        # Store resource
        self.processor_resources[processor_id] = processor_resource
        
        # if self.logger:
        #     self.logger.log_event(
        #         "Resource", f"Registered {processor.type_processor} {processor_name} to process {self.name_process}")
        
    def add_to_queue(self, item):
        """Add item to queue"""
        item.time_waiting_start = self.env.now
        
        if not hasattr(item, 'process_sequence'):
            item.process_sequence = []
        item.process_sequence.append(self.name_process)

        # Record item waiting history
        process_step = self.create_waiting_step(item)
        if not hasattr(item, 'waiting_history'):
            item.waiting_history = []
        item.waiting_history.append(process_step)        

        # Add item to itemStore
        self.item_store.put(item)

        # Trigger item added event
        self.item_added_trigger.succeed()
        # Create new trigger immediately
        self.item_added_trigger = self.env.event()

        if self.logger:
            self.logger.log_event(
                "Queue", f"Added item {item.id_item} to {self.name_process} queue. Queue length: {self.item_store.size}")

    def run(self):
        "Event based process execution"
        
        if not self.item_store.is_empty:
            yield self.env.process(self.seize_resources())
            
        while True:
            # Wait for events: until item is added or resource is released
            yield self.item_added_trigger | self.resource_trigger
            
            # If there are items in queue, attempt to allocate resources
            if not self.item_store.is_empty:
                yield self.env.process(self.seize_resources())
    
    def seize_resources(self):
        """
        Allocate available resources (machines or Amrs or workers) to items in queue
        """
        # print(
        #     f"[DEBUG] {self.name_process}: seize_resources called, time={self.env.now}")

        # Find available processors
        available_processors = [
            res for res in self.processor_resources.values() if res.is_available]

        # print(
        #     f"[DEBUG] {self.name_process}: available processors={len(available_processors)}")
        # Debug: Print status of each resource
        # for res_id, res in self.processor_resources.items():
        #     print(
        #         f"[DEBUG] Processor {res_id}: is_available={res.is_available}, capacity={res.capacity}")

        # If queue is empty or no available processors, stop
        if self.item_store.is_empty or not available_processors:
            # print(
            #     f"[DEBUG] {self.name_process}: item allocation stopped - queue empty={self.item_store.is_empty}, no processors={not available_processors}")
            return

        # List of items assigned to each processor
        processor_assignments = []

        # Try processing with all processors
        for processor_resource in available_processors:
            # print(
            #     f"[DEBUG] {self.name_process}: attempting to process with {processor_resource.name}")
            # Determine number of items to assign (up to capacity)
            remaining_capacity = processor_resource.capacity - processor_resource.count
            items_to_assign = []

            # Assign items
            try:
                for i in range(min(remaining_capacity, self.item_store.size)):
                    if not self.item_store.is_empty:
                        # print(
                        #     f"[DEBUG] {self.name_process}: attempting to get item {i+1}")
                        item = yield self.item_store.get()
                        # print(
                        #     f"[DEBUG] {self.name_process}: retrieved item {item.id_item}")
                        items_to_assign.append(item)
            except Exception as e:
                # Continue if unable to get item from itemStore
                print(f"[ERROR] {self.name_process}: failed to get item: {e}")

            # Assign items to processor
            if items_to_assign:
                processor_assignments.append(
                    (processor_resource, items_to_assign))
                # yield self.env.process(self.delay_resources(processor_resource, items_to_assign))

        # Process items with assigned processors in parallel
        for processor_resource, items in processor_assignments:
            self.env.process(self.delay_resources(processor_resource, items))
            
    def delay_resources(self, processor_resource, items):
        """
        Process items with processor (integrated for Machine, Amr, Worker)
        Takes processing time into account 

        Args:
            processor_resource (ProcessorResource): Processor resource (Machine, Amr, Worker)
            items (list): List of items to process        
        """
        # Record time and register resources for all items
        for item in items:
            item.time_waiting_end = self.env.now

            # Update item history
            for step in item.waiting_history:
                if step['process'] == self.name_process and step['end_time'] is None:
                    step['end_time'] = self.env.now
                    step['duration'] = self.env.now - step['start_time']

            # Register item with processor
            processor_resource.start_item(item)

            if self.logger:
                self.logger.log_event(
                    "Processing", f"Assigning item {item.id_item} to {processor_resource.name}")

            # Record item start time
            item.time_processing_start = self.env.now

            # Record item processing history
            process_step = self.create_process_step(item, processor_resource)
            if not hasattr(item, 'processing_history'):
                item.processing_history = []
            item.processing_history.append(process_step)

        # Request processor resource
        request = processor_resource.request()
        yield request
        
        # Calculate and wait for dynamic processing time
        if hasattr(self, 'calculate_processing_time'):
            self.calculate_processing_time(processor_resource.processing_time, items)
            for item in items:
                processing_time = item.processing_time
                yield self.env.timeout(processing_time)
        
        else:
            processing_time = processor_resource.processing_time
                
            yield self.env.timeout(processing_time)

        # Special processing (if needed)
        if hasattr(self, 'apply_special_processing'):
            self.apply_special_processing(processor_resource.processor, items)

        # Process item completion
        for item in items:
            item.time_processing_end = self.env.now

            # Update item history
            for step in item.processing_history:
                if step['process'] == self.name_process and step['end_time'] is None:
                    step['end_time'] = self.env.now
                    step['duration'] = self.env.now - step['start_time']

            # Track completed items
            self.completed_items.append(item)

            # Log record
            if self.logger:
                self.logger.log_event(
                    "Processing", f"Completed processing item {item.id_item} on {processor_resource.name}")

            # Send item to next process
            self.send_item_to_next(item)

        # Release resources
        self.release_resources(processor_resource, request)
        
    def release_resources(self, processor_resource, request):
        """
        Release processor resources and process item completion

        Args:
            processor_resource (ProcessorResource): Processor resource (Machine, Worker)
            request (simpy.Request): Resource request 

        """
        # Release processor resource
        processor_resource.release(request)
        processor_resource.finish_items()

        # Trigger resource release event (for event-based approach)
        if hasattr(self, 'resource_trigger'):
            self.resource_trigger.succeed()
            # Create new trigger immediately
            self.resource_trigger = self.env.event()

        if self.logger:
            self.logger.log_event(
                "Resource", f"Released {processor_resource.name} in {self.name_process}")

    def create_process_step(self, item, processor_resource):
        """Create process step for item history"""
        return {
            'process': self.name_process,
            'resource_type': processor_resource.processor_type,
            'resource_id': processor_resource.id,
            'resource_name': processor_resource.name,
            'start_time': item.time_processing_start,
            'end_time': None,
            'duration': None
        }

    def create_waiting_step(self, item):
        """Create waiting step for item history"""
        return {
            'process': self.name_process,
            'start_time': item.time_waiting_start,
            'end_time': None,
            'duration': None
        }
    
    def send_item_to_next(self, item):
        """Send item to next process"""
        if self.next_process:
            if self.logger:
                self.logger.log_event(
                    "Process Flow", f"Moving item {item.id_item} from {self.name_process} to {self.next_process.name_process}")
            # Add item to next process queue
            self.next_process.add_to_queue(item)
            return True
        else:
            # Final process or no next process set
            if self.logger:
                self.logger.log_event(
                    "Process Flow", f"item {item.id_item} completed at {self.name_process} (final process)")
            return False