"""SQLAlchemy models.

All models inherit from the shared Base in app.db, so importing this module
registers their tables on Base.metadata (which Base.metadata.create_all reads).
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True, nullable=False)  # Rails JWT sub
    created_at = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="recipient")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    recipient_id = Column(Integer, ForeignKey("recipients.id"), index=True, nullable=False)
    name = Column(String)          # human label, e.g. "Moin's MacBook"
    platform = Column(String)      # e.g. "macos", "android"
    user_agent = Column(String)    # raw UA string, to tell browsers apart
    created_at = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("Recipient", back_populates="devices")
    subscriptions = relationship("Subscription", back_populates="device")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True, nullable=False)
    endpoint = Column(String, unique=True, nullable=False)  # push URL — where to POST
    p256dh = Column(String, nullable=False)                 # keys.p256dh (encryption)
    auth = Column(String, nullable=False)                   # keys.auth (encryption)
    expiration_time = Column(DateTime, nullable=True)       # usually null
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="subscriptions")
