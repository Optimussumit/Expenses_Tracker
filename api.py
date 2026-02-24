from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel
from typing import List

DATABASE_URL = "sqlite:///./expenses.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------- DATABASE MODEL ---------------- #

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    type = Column(String, nullable=False)
    date = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# ---------------- API ---------------- #

app = FastAPI(title="Expense Tracker API")

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    type: str
    date: str

@app.post("/expenses")
def add_expense(expense: ExpenseCreate):
    db = SessionLocal()
    new_expense = Expense(**expense.dict())
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    db.close()
    return new_expense

@app.get("/expenses", response_model=List[ExpenseCreate])
def get_expenses():
    db = SessionLocal()
    data = db.query(Expense).all()
    db.close()
    return data