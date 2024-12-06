from sqlalchemy.orm import Session

from database_courier import engine
from models_courier import DeliveryMan, DeliveryManStatuses
import random
from sqlalchemy.exc import SQLAlchemyError
import time


def assign_order_to_courier(order_id, max_retries=5, retry_interval=5):
    retries = 0

    try:
        while retries < max_retries:
            with Session(engine) as session:
                available_couriers = session.query(DeliveryMan).filter(
                    DeliveryMan.status == DeliveryManStatuses.available
                ).all()

                if available_couriers:
                    selected_courier = random.choice(available_couriers)
                    selected_courier.status = DeliveryManStatuses.busy
                    session.commit()
                    print(
                        f"Assigned order {order_id} to courier {selected_courier.fio_courier} (ID: {selected_courier.courier_id})",
                        flush=True,
                    )
                    return selected_courier.courier_id

            print(
                f"No available couriers for order {order_id}. Retrying in {retry_interval} seconds...",
                flush=True,
            )
            retries += 1
            time.sleep(retry_interval)

        print(
            f"Failed to assign courier for order {order_id} after {max_retries} attempts. Cancel the order manually",
            flush=True,
        )
        # cancel_order(order_id, session)  # Ранее неактивный код. Здесь тоже нужно учитывать контекстный менеджер
        return None
    except SQLAlchemyError as e:
        print(f"Database error: {e}", flush=True)

def initialize_delivery_man():
    predefined_delivery_men = [
        DeliveryMan(fio_courier="Иван Иванов", status=DeliveryManStatuses.available),
        DeliveryMan(fio_courier="Петр Петров", status=DeliveryManStatuses.available),
        DeliveryMan(fio_courier="Михаил Михайлов", status=DeliveryManStatuses.not_working),
    ]
    try:
        with Session(engine) as session:
            for delivery_man in predefined_delivery_men:
                session.add(delivery_man)
            session.commit()
            print("Predefined delivery men have been initialized.", flush=True)
    except Exception as e:
        print(f"Error initializing delivery men: {e}", flush=True)

def free_courier(courier_id):
    try:
        with Session(engine) as session:
            courier = session.query(DeliveryMan).filter(DeliveryMan.courier_id == courier_id).first()
            if courier:
                courier.status = DeliveryManStatuses.available
                session.commit()
                print(f"Status of courier {courier_id} updated to 'available'.", flush=True)
            else:
                print(f"Courier {courier_id} not found.", flush=True)
    except SQLAlchemyError as e:
        print(f"Database error: {e}", flush=True)