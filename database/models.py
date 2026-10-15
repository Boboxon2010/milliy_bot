from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    selected_subject = Column(String(255), nullable=True)
    balance = Column(Integer, default=0, nullable=True)
    phone_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    essay_topics = relationship("UserEssayTopic", back_populates="user", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="user", cascade="all, delete-orphan")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(100), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="single")  # 'single' yoki 'text'
    difficulty = Column(Integer, default=1)  # 1, 2, 3
    option_a = Column(String(255), nullable=True)
    option_b = Column(String(255), nullable=True)
    option_c = Column(String(255), nullable=True)
    option_d = Column(String(255), nullable=True)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, default="", nullable=True)


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(100), nullable=False)
    raw_score = Column(Integer, default=0, nullable=True)
    t_score = Column(Float, default=0.0, nullable=True)
    level = Column(Text, default="", nullable=True)
    time_spent_seconds = Column(Integer, default=0, nullable=True)
    correct_count = Column(Integer, default=0, nullable=True)
    answered_count = Column(Integer, default=45, nullable=True)
    total_questions = Column(Integer, default=45, nullable=True)
    score = Column(Float, default=0.0, nullable=True)
    is_completed = Column(Boolean, default=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="results")


class UserError(Base):
    __tablename__ = "user_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class UserEssayTopic(Base):
    __tablename__ = "user_essay_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    topic_text = Column(Text, nullable=False)
    essay_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="essay_topics")