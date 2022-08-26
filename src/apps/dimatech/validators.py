from typing import Optional

from pydantic import BaseModel, Field


class ProductValidator(BaseModel):
    title: str = Field(max_length=50)
    description: Optional[str]
    price: float = Field(ge=0.0)


class CustomerBillValidator(BaseModel):
    user_id: int
    balance: float = Field(ge=0.0)


class TransactionValidator(BaseModel):
    transaction_id: Optional[int]
    user_id: int
    bill_id: int
    amount: float = Field(ge=0.0)


class PurchaseValidator(BaseModel):
    product_id: int
    user_id: int
    bill_id: int
