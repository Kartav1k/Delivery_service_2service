from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "postgresql://postgres:123456@delivery-db:5432/orders_delivery"
engine = create_engine(DATABASE_URL)
#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)