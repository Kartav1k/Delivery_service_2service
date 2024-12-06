from sqlalchemy.orm import Session

from database import engine
from models import Orders, DeliveryStatuses

def add_courier_to_delivery(id_order, courier_id):
    try:
        with Session(engine) as session:
            order = session.query(Orders).filter(Orders.id_order == id_order).first()
            if order:
                order.status = DeliveryStatuses.accepted
                order.courier_id = courier_id
                session.commit()
                print(f"Order {id_order} status updated to 'accepted' with courier ID {courier_id}")
            else:
                print(f"Order with ID {id_order} not found")
    except Exception as e:
        print(f"Error updating order: {e}")