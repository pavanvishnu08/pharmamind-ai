"""
PharmaMind AI - Conversation and Message Models
"""

import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Biomedical Consultation", nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Structured evidence grounding
    direct_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    drug_information: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence_status: Mapped[str] = mapped_column(String(50), default="VERIFIED_AUTHORITATIVE", nullable=False)
    safety_disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Informational purpose only. Not clinical or prescribing advice. Consult a healthcare professional.",
        nullable=False
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

