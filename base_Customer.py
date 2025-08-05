from config_SimPy import *

class Item:
    """
    Class representing an item in the system.
    
    Attribute:
    id_customer: ID of the customer this item belongs to
    id_order: ID of the order this item belongs to
    id_item: ID of this item
    type_item: Type of item (e.g., bolt, nut, ...)
    is_completed: Flag indicating if the manufacturing of the item is completed
    is_defect: Flag indicating if the item is defective
    workstation (dict): Current workstation assignment
    time_processing_start (float): Time when processing started
    time_processing_end (float): Time when processing ended
    time_waiting_start (float): Time when waiting started
    time_waiting_end (float): Time when waiting ended
    is_reprocess (bool): Flag for reprocessed item
    processing_history (list): List of processing history
    is_supplier: Item of Order type is lot or pallet.
    """
    
    def __init__(self, id_customer, id_order, id_item, is_supplier):
        self.id_customer = id_customer
        self.id_order = id_order
        self.id_item = id_item
        self.type_item = "smartphone"  # default
        self.is_completed = False
        self.is_defect = False
        self.workstation = {"Process": None, "Machine": None, "Worker": None}
        self.time_processing_start = None
        self.time_processing_end = None
        self.time_waiting_start = None
        self.time_waiting_end = None
        self.is_reprocess = False  # Flag for reprocessed item
        # Add processing history to track items across all processes and waiting
        self.processing_history = []  # Will store each process step details
        self.waiting_history = []  # Will store each waiting step details
        self.is_supplier = is_supplier
        
class Order:
    """
    Class representing an order in the system.

    Attributes:
        id_customer: ID of the customer this order belongs to
        id_order: ID of this order
        num_items: Number of items for this order
        list_items: List of items for this order
        time_start: Start time of this order
        time_end: End time of this order
        item_counter: Counter for item IDs
        completed_item_count: Counter for completed items
        makespan: Makespan of this order
        order_supplier: Item of Order type is lot or pallet.
    """

    def __init__(self,  id_customer, id_order, order_supplier):
        """
        Create an order with the given ID.

        Args:
            id_customer: ID of the customer this item belongs to
            id_order:    ID of the order this item belongs to
        """
        self.id_customer = id_customer
        self.id_order = id_order
        self.num_items = NUM_ITEMS_PER_ORDER()
        self.list_items = []
        self.time_start = None
        self.time_end = None
        self.item_counter = 1
        self.completed_item_count = 0
        self.makespan = None
        self.is_supplier = order_supplier
        
        # Create items for this order using the provided function
        self.list_items = self._create_items_for_order(
            self.id_customer, self.id_order, self.num_items, self.is_supplier)

    def _create_items_for_order(self, id_customer, id_order, num_items, is_supplier):
        """Create items for an order"""
        items = []
        for _ in range(num_items):
            item_id = self._get_next_item_id()
            item = Item(id_customer, id_order, item_id, is_supplier)
            items.append(item)
        return items

    def _get_next_item_id(self):
        """Get next item ID and increment counter"""
        item_id = self.item_counter
        self.item_counter += 1
        return item_id

    def check_completion(self):
        """Check if all items for this order are completed"""
        if all(item.is_completed for item in self.list_items):
            self.is_completed = True
        return False
    
class Customer:
    """
    Class representing a customer in the system.
    
    Attributes:
    env: Simulation envrionment
    order_receiver: Order receiver object
    logger: Logger object
    id_customer: ID of this customer
    """
    
    # Counter for creating global unique customer_id
    _next_customer_id = 1
    
    def __init__(self, env, order_receiver, logger):
        self.env = env
        self.order_receiver = order_receiver
        self.logger = logger
        # Assign a Customer-Specific ID
        self.id_customer = Customer._next_customer_id
        Customer._next_customer_id += 1
        
        # Initialize ID counters
        self.order_counter = 1
        
        # Automatically start the process when the Customer is created
        self.processing = env.process(self.create_order())

    def get_next_order_id(self):
        """Get next order ID and increment counter"""
        order_id = self.order_counter
        self.order_counter += 1
        return order_id
            
    def create_order(self):
        """Create orders periodically"""
        while True:
            # Create a new order
            order_id = self.get_next_order_id()
            order_supplier = SUPPLY_TYPE_DECISION()
            order = Order(self.id_customer, order_id, order_supplier)
            order.time_start = self.env.now

            # # Log order creation
            # self.logger.log_event(
            #     "Order", f"Created Order {order.id_order}, Total items: {sum(len(order.list_items) for order in order.list_items)})")

            # Send the order
            self.send_order(order)

            # Wait for next order cycle
            yield self.env.timeout(CUST_ORDER_CYCLE)
            
    def send_order(self, order):
        """Send the order to the receiver"""
        # if self.logger:
        #     self.logger.log_event(
        #         "Order", f"Sending Order {order.id_order} to processor")
        self.order_receiver.receive_order(order)


class OrderReceiver:
    """Interface for order receiving objects"""

    def receive_order(self, order):
        """Method to process orders (implemented by subclasses)"""
        pass
    
# --- file: base_Customer.py 끝에 추가 ---

if __name__ == "__main__":
    import simpy

    class DummyReceiver(OrderReceiver):
        def __init__(self):
            # (선택) 받은 주문을 나중에 확인하고 싶다면 저장해두어도 좋습니다.
            self.received_orders = []

        def receive_order(self, order):
            # 요청이 들어올 때마다 order 저장
            self.received_orders.append(order)

            # item.id_item 리스트 추출
            item_ids = [item.id_item for item in order.list_items]

            # env.now를 쓰기 위해 전역 env를 참조
            print(f"[{env.now} 분] 주문 수신: "
                  f"고객ID={order.id_customer}, 주문ID={order.id_order}, "
                  f"아이템수={len(order.list_items)}, "
                  f"아이템IDs={item_ids}, Order type:{order.is_supplier}")

    # 시뮬레이션 환경과 리시버 생성
    env = simpy.Environment()
    receiver = DummyReceiver()

    # Customer 생성 (order_receiver로 DummyReceiver 전달)
    customer = Customer(env, order_receiver=receiver, logger=None)

    # 시뮬레이션 실행 (한 사이클만 보고 싶으면 until=CUST_ORDER_CYCLE)
    env.run(SIM_TIME)

    print("=== 시뮬레이션 종료 ===")
