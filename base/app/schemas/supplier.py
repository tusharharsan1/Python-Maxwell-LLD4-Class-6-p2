"""The gate for data that comes in from the supplier. EXAMPLE, already finished.

(This is the finished model from the last problem. You do not need to change it.)
"""
from pydantic import BaseModel, Field


class Dimensions(BaseModel):
    width: float
    height: float
    depth: float


class SupplierProduct(BaseModel):
    id: int
    title: str
    description: str
    category: str
    price: float
    stock: int
    image_url: str = Field(alias="thumbnail")
    discount_percentage: float = Field(alias="discountPercentage")
    dimensions: Dimensions | None = None
