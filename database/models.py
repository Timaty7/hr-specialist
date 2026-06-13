import enum
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class UserRole(enum.Enum):
    GUEST = "guest"
    CANDIDATE = "candidate"
    EMPLOYER = "employer"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.GUEST)
    balance = Column(Float, default=0.0)
    referrer_id = Column(Integer, nullable=True)
    is_subscribed = Column(Boolean, default=False)
    subscription_expires = Column(DateTime, nullable=True)
    
    # Работодатель лимиттері (ТЗ 10.5)
    opened_candidates_count = Column(Integer, default=0)
    max_candidates_limit = Column(Integer, default=0)  # 20 немесе 50

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    position = Column(String)
    experience = Column(Integer)
    prev_jobs = Column(String)
    schedule = Column(String)
    salary = Column(Integer)
    contact = Column(String)

class Vacancy(Base):
    __tablename__ = "vacancies"
    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("users.id"))
    company_name = Column(String)
    city = Column(String)
    position = Column(String)
    requirements = Column(String)
    conditions = Column(String)
    salary = Column(Integer)
    schedule = Column(String)
    address = Column(String)
    contact_person = Column(String)
    phone = Column(String)

class WithdrawalRequest(Base):
    """ТЗ 11.6: Баланстан ақша шығару сұраныстарының кестесі"""
    __tablename__ = "withdrawal_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    phone_number = Column(String, nullable=False)  # Kaspi үшін
    status = Column(String, default="Pending")  # Pending, Approved, Rejected
    created_at = Column(DateTime, default=datetime.utcnow)