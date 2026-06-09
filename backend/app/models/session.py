import uuid
from sqlalchemy import Column, String, DateTime, func

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
