from .enums import Currency, UserStatus, AccountStatus, TransactionStatus, TransactionError

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Numeric,
    Enum as SqlEnum,
)

from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class User(Base):
    """
    Model for user; used for auth and all.
    """
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(SqlEnum(UserStatus), nullable=False)


class Account(Base):
    """
    Model for account; used to track source/destination of funds
    plus its status and balance.
    """
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    balance = Column(Numeric(16,8), nullable=False)
    currency = Column(SqlEnum(Currency), nullable=False)
    status = Column(SqlEnum(AccountStatus), nullable=False)

class Transaction(Base):
    """
    Model for transaction; used to track actual movements of money
    and the source/destination.
    """
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("account.id"), nullable=False)
    amount = Column(Numeric(16,8), nullable=False)
    status = Column(SqlEnum(TransactionStatus), nullable=False)
    error_code = Column(SqlEnum(TransactionError), nullable=True)

