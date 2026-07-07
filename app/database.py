from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, MetaData, DateTime, text
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from .db import metadata


@as_declarative()
class Base:
    """
    Base class to handle table schema
    """
    __name__: str

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    @declared_attr
    def metadata(cls) -> MetaData:
        return metadata

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def to_dict(self) -> dict[str, object]:
        """
        Convert a SQLAlchemy model instance into a dictionary suitable
        for JSON serialization.
        """
        result = {}

        for column in self.__table__.columns:
            value = getattr(self, column.name)

            if isinstance(value, Enum):
                result[column.name] = value.value

            elif isinstance(value, UUID):
                result[column.name] = str(value)

            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()

            elif isinstance(value, Decimal):
                result[column.name] = str(value)
                # Alternatively: float(value)

            else:
                result[column.name] = value

        return result
