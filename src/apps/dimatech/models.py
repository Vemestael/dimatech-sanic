from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from apps.auth.models import User

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)


class ProductModel(BaseModel):
    """
    Consists of:
    title: String(50)
    description: String
    price: Numeric
    """
    __tablename__ = 'product'

    title = Column(String(50), nullable=False)
    description = Column(String, default='')
    price = Column(Numeric, default=0.0, nullable=False)


class CustomerBillModel(BaseModel):
    """
    Consists of:
    user_id: ForeignKey to User
    balance: Numeric
    """
    __tablename__ = 'customer_bill'
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    balance = Column(Numeric, default=0.0, nullable=False)

    user = relationship(User, backref='customer_bill')


class TransactionModel(BaseModel):
    """
    Consists of:
    user_id: ForeignKey to User
    bill_id: ForeignKey to CustomerBillModel
    amount: Numeric
    """
    __tablename__ = 'transaction'

    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    bill_id = Column(Integer, ForeignKey('customer_bill.id'), nullable=False)
    amount = Column(Numeric, default=0.0, nullable=False)

    user = relationship(User, backref='transaction')
    bill = relationship(CustomerBillModel, backref='transaction')


class PurchaseModel(BaseModel):
    """
    Consists of:
    product_id: ForeignKey to ProductModel
    user_id: ForeignKey to User
    bill_id: ForeignKey to CustomerBillModel
    """
    __tablename__ = 'purchase'

    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    bill_id = Column(Integer, ForeignKey('customer_bill.id'), nullable=False)

    product = relationship(ProductModel, backref='purchase')
    user = relationship(User, backref='purchase')
    bill = relationship(CustomerBillModel, backref='purchase')
