from enum import Enum

class Currency(Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    BTC = "BTC"
    ETH = "ETH"

class UserStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    UNDER_INVESTIGATION = "under_investigation"
    DORMANT = "dormant"
    CLOSED = "closed"

class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

class TransactionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TransactionError(Enum):
    UNKNOWN_ACCOUNT = "unknown_account"
    INVALID_OPERATION = "invalid_operation"
    INVALID_CURRENCY = "invalid_currency"
    INSUFFICIENT_BALANCE = "insufficient_balance"