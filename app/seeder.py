"""Seed the database with sample users, accounts, and transaction history.

Idempotent: skips seeding if data already exists, so re-running the
container (e.g. on every `docker compose up`) does not duplicate rows.
"""

import random
from decimal import Decimal

from .db import LocalSession, metadata, engine
from .auth.models import User, Account, Transaction
from .auth.enums import (
    Currency,
    UserStatus,
    AccountStatus,
    TransactionStatus,
    TransactionError,
)
from .auth.services import hash_password


NUM_ACCOUNTS = 12
NUM_TRANSACTIONS = 40
SEED_PASSWORD = "Password123!"  # dev/seed-only, not a real credential

CURRENCIES = [Currency.EUR, Currency.USD, Currency.GBP]


def _seed_users_and_accounts(db):
    accounts = []
    for i in range(NUM_ACCOUNTS):
        user = User(
            email=f"user{i + 1}@feybank.test",
            password_hash=hash_password(SEED_PASSWORD),
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()  # populate user.id before using it as a FK

        account = Account(
            user_id=user.id,
            balance=Decimal(random.randint(100, 10000)),
            currency=random.choice(CURRENCIES),
            status=AccountStatus.ACTIVE,
        )
        db.add(account)
        accounts.append(account)

    db.flush()  # populate account.id for all accounts before transactions
    return accounts


def _seed_transactions(db, accounts):
    """
    Mirrors, approximately, the load generator's eventual traffic profile
    (85% success / 10% insufficient balance / 5% other failure), so early
    dashboards and queries have a non-trivial mix to work with even before
    the load generator (Layer 0, still pending) starts producing live traffic.
    """
    for _ in range(NUM_TRANSACTIONS):
        from_acc, to_acc = random.sample(accounts, 2)
        amount = Decimal(random.randint(1, 500))

        roll = random.random()
        if roll < 0.85:
            status = TransactionStatus.COMPLETED
            error_code = None
        elif roll < 0.95:
            status = TransactionStatus.FAILED
            error_code = TransactionError.INSUFFICIENT_BALANCE
        else:
            status = TransactionStatus.FAILED
            error_code = TransactionError.INVALID_OPERATION

        transaction = Transaction(
            from_account_id=from_acc.id,
            to_account_id=to_acc.id,
            amount=amount,
            status=status,
            error_code=error_code,
        )
        db.add(transaction)


def seeder():
    # `db.py` runs metadata.create_all(engine) at import time, before the
    # model classes below are registered on `metadata` — so tables don't
    # exist yet at that point. Re-running create_all here, now that the
    # models are imported and registered, creates whatever is still missing.
    # Safe to call repeatedly: create_all only creates tables that don't exist.
    metadata.create_all(engine)

    db = LocalSession()
    try:
        already_seeded = db.query(User).first() is not None
        if already_seeded:
            print("Seeder: data already present, skipping.")
            return

        accounts = _seed_users_and_accounts(db)
        _seed_transactions(db, accounts)
        db.commit()
        print(
            f"Seeder: created {len(accounts)} accounts "
            f"and {NUM_TRANSACTIONS} transactions."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seeder()