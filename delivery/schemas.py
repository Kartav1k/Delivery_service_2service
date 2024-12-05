from pydantic import BaseModel

class DeliveryCreate(BaseModel):
    customer: str
    address: str
    is_pickup: bool = False

    class Config:
        from_attributes = True