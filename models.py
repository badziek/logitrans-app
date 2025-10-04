from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum, Float, Boolean, Date, Time, UniqueConstraint, Index
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class Role(enum.Enum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    USER = "USER"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    loads: Mapped[list["Load"]] = relationship(back_populates="created_by")
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def get_id(self):
        return str(self.id)

class Shift(enum.Enum):
    A = "A"
    B = "B"
    C = "C"

class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    time_slot: Mapped[str] = mapped_column(String(5), index=True, default="17:00")
    trailer_no: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    lane: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)   # L01/L02/L03
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    done: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lo_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    picker: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)   # PL/PA/LO
    confirmed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    vehicle_no: Mapped[str] = mapped_column(String(50), index=True, default="")
    order_no: Mapped[str] = mapped_column(String(100), default="")
    payload_tons: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # NOWE KOLUMNY
    ship_date: Mapped[str | None] = mapped_column(String(20), nullable=True)   # <-- dodaliśmy
    area: Mapped[str | None] = mapped_column(String(10), nullable=True)        # <-- dodaliśmy

    shift: Mapped[Shift] = mapped_column(Enum(Shift))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped["User"] = relationship(back_populates="loads")


