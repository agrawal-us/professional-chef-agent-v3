from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, UniqueConstraint, func

from app.database import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    template = Column(Text, nullable=False)
    active = Column(Boolean, default=False, nullable=False)
    thumbs_up_rate = Column(Float)
    sample_count = Column(Integer, default=0)
    notes = Column(Text)
    effective_date = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deprecated_date = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("prompt_name", "version", name="uq_prompt_versions_name_version"),
    )
