from sqlalchemy import create_engine

from models_courier import Base

DATABASE_URL = "postgresql://postgres:123456@courier-db:5432/courier_service"
engine = create_engine(DATABASE_URL)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)