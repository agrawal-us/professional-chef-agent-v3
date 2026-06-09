from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func

from app.database import Base


class GenerationLog(Base):
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cache_hit = Column(Boolean, default=False, nullable=False)
    generation_model = Column(String(100))
    generation_provider = Column(String(50))
    prompt_version = Column(String(20))
    user_feedback = Column(String(20))
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
