from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    role = Column(String(50))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TaskMemory(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    status = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

class MemoryManager:
    def __init__(self, db_path="sqlite:///radmir_memory.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_message(self, role: str, content: str):
        session = self.Session()
        msg = ChatMessage(role=role, content=content)
        session.add(msg)
        session.commit()
        session.close()

    def get_history(self, limit=50):
        session = self.Session()
        msgs = session.query(ChatMessage).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        session.close()
        return [{"role": m.role, "content": m.content, "time": m.timestamp} for m in msgs]
