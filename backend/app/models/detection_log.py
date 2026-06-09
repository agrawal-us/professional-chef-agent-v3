from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from app.database import Base


class DetectionLog(Base):
    __tablename__ = "detection_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String,
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    detection_model = Column(String(100))
    prompt_version = Column(String(20))
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
