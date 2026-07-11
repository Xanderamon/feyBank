"""Database seeder — not yet implemented."""

from .db import LocalSession
from .auth.models import User, Account, Transaction


def seeder():
    """
    Placeholder. Layer 0 requires the container to exit cleanly;
    actual seed logic (>=10 accounts + transaction history) is
    still to be implemented per feyBank Project Definition, Layer 0 deliverables.
    """
    pass


if __name__ == "__main__":
    seeder()