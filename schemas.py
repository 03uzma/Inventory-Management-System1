from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: int


class StockUpdate(BaseModel):
    change: int