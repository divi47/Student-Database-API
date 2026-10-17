from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
app = FastAPI()
# 1. SQLite Database Setup
DATABASE_URL = "sqlite:///./students.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Database Model
class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date_of_birth = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    course = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# 3. Pydantic Models (Validation)
class StudentCreate(BaseModel):
    name: str
    date_of_birth: str
    email: str
    phone: str
    course: Optional[str] = None

class StudentResponse(StudentCreate):
    id: int

    class Config:
        from_attributes = True

# 4. FastAPI Application Setup
app = FastAPI(title="Student Database CRUD API")

# Dependency to get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- CRUD ENDPOINTS -----------------

# 1. CREATE Student
@app.post("/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = StudentDB(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# 2. READ All Students
@app.get("/students", response_model=List[StudentResponse])
def get_all_students(db: Session = Depends(get_db)):
    return db.query(StudentDB).all()

# 3. READ Single Student
@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# 4. UPDATE Student
@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, updated_data: StudentCreate, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    for key, value in updated_data.model_dump().items():
        setattr(student, key, value)
        
    db.commit()
    db.refresh(student)
    return student

# 5. DELETE Student
@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(student)
    db.commit()
    return {"message": f"Student with ID {student_id} deleted successfully"}