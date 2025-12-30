import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

# ==========================================
# 1. DATABASE CONFIGURATION
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sitetrack.db")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. DATABASE MODELS
# ==========================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)

class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    engineer = Column(String)
    location = Column(String)
    unit = Column(String)
    planned_qty = Column(String)
    achieved_qty = Column(String)
    description = Column(String)
    subcontractor = Column(String)
    delay_reason = Column(String)
    date = Column(String)

class WorkerReport(Base):
    __tablename__ = "worker_reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    engineer = Column(String)
    location = Column(String)
    subcontractor = Column(String)
    masons = Column(String)
    helpers = Column(String)
    description = Column(String)
    date = Column(String)

class MaterialIndent(Base):
    __tablename__ = "material_indents"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id")) 
    item_name = Column(String)              
    quantity = Column(String)               
    priority = Column(String)               
    status = Column(String, default="Pending")
    requested_by = Column(String)           
    date = Column(String)                   

class MaterialQuotation(Base):
    __tablename__ = "material_quotations"
    id = Column(Integer, primary_key=True, index=True)
    indent_id = Column(Integer, ForeignKey("material_indents.id"))
    vendor_name = Column(String)
    price = Column(Float)
    is_approved = Column(Boolean, default=False)

# ==========================================
# 3. FORCE DATABASE RESET (RAW SQL)
# ==========================================
# This block MANUALLY deletes the tables to fix the "UndefinedColumn" error.
try:
    with engine.connect() as connection:
        connection.execute(text("DROP TABLE IF EXISTS daily_reports CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS worker_reports CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS material_quotations CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS material_indents CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
        connection.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        connection.commit()
    print("--- TABLES DROPPED SUCCESSFULLY ---")
except Exception as e:
    print(f"--- ERROR DROPPING TABLES: {e} ---")

# Now create them fresh
Base.metadata.create_all(bind=engine)

# ==========================================
# 4. SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    phone_number: str
    password: str

class UserCreate(BaseModel):
    name: str
    phone_number: str
    password: str
    role: str = "admin"

class ProjectCreate(BaseModel):
    name: str
    location: str

class ReportSchema(BaseModel):
    project_id: int
    engineer: str
    location: str
    unit: str
    planned_qty: str
    achieved_qty: str
    description: str
    subcontractor: str
    delay_reason: str
    date: str

class WorkerSchema(BaseModel):
    project_id: int
    engineer: str
    location: str
    subcontractor: str
    masons: str
    helpers: str
    description: str
    date: str

class IndentCreate(BaseModel):
    project_id: int
    item_name: str
    quantity: str
    priority: str = "Medium"
    requested_by: str
    date: str

class QuotationCreate(BaseModel):
    indent_id: int
    vendor_name: str
    price: float

class ApprovalUpdate(BaseModel):
    indent_id: int
    selected_quotation_id: int

# ==========================================
# 5. APP & ROUTES
# ==========================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "SiteTrack Server is Live!"}

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if existing_user:
        # If user exists, just return success to avoid error during testing
        return {"message": "User already exists", "user_id": existing_user.id}
    
    new_user = User(
        name=user.name, 
        phone_number=user.phone_number, 
        password=user.password, 
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "user_id": new_user.id}

@app.post("/login")
def login(user_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == user_req.phone_number).first()
    if not user or user.password != user_req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "status": "success",
        "user_id": user.id,
        "name": user.name,
        "role": user.role,
        "token": "fake_token_123"
    }

@app.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@app.post("/projects")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    new_project = Project(name=project.name, location=project.location)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"detail": "Project deleted"}

@app.put("/projects/{project_id}")
def update_project(project_id: int, project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_project.name = project.name
    db_project.location = project.location
    db.commit()
    return db_project

@app.post("/daily-reports")
def create_report(report: ReportSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project ID {report.project_id} not found")

    new_report = DailyReport(**report.dict())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@app.get("/daily-reports/{project_id}")
def get_daily_reports(project_id: int, db: Session = Depends(get_db)):
    return db.query(DailyReport).filter(DailyReport.project_id == project_id).all()

@app.post("/worker-reports")
def create_worker_report(report: WorkerSchema, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project ID {report.project_id} not found")

    new_report = WorkerReport(**report.dict())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@app.get("/worker-reports/{project_id}")
def get_worker_reports(project_id: int, db: Session = Depends(get_db)):
    return db.query(WorkerReport).filter(WorkerReport.project_id == project_id).all()

@app.post("/create_indent")
def create_material_indent(indent: IndentCreate, db: Session = Depends(get_db)):
    new_indent = MaterialIndent(
        project_id=indent.project_id,
        item_name=indent.item_name,
        quantity=indent.quantity,
        priority=indent.priority,
        requested_by=indent.requested_by,
        date=indent.date,
        status="Pending"
    )
    db.add(new_indent)
    db.commit()
    db.refresh(new_indent)
    return {"message": "Indent raised successfully", "id": new_indent.id}

@app.get("/get_indents/{project_id}")
def get_indents(project_id: int, db: Session = Depends(get_db)):
    return db.query(MaterialIndent).filter(MaterialIndent.project_id == project_id).all()

@app.post("/add_quotation")
def add_quotation(quote: QuotationCreate, db: Session = Depends(get_db)):
    indent = db.query(MaterialIndent).filter(MaterialIndent.id == quote.indent_id).first()
    if not indent:
        raise HTTPException(status_code=404, detail="Indent ID not found")
    
    new_quote = MaterialQuotation(
        indent_id=quote.indent_id,
        vendor_name=quote.vendor_name,
        price=quote.price
    )
    indent.status = "Quoted"
    db.add(new_quote)
    db.commit()
    return {"message": "Quotation added successfully"}

@app.get("/get_quotes/{indent_id}")
def get_quotes(indent_id: int, db: Session = Depends(get_db)):
    return db.query(MaterialQuotation).filter(MaterialQuotation.indent_id == indent_id).all()

@app.post("/approve_indent")
def approve_indent(approval: ApprovalUpdate, db: Session = Depends(get_db)):
    indent = db.query(MaterialIndent).filter(MaterialIndent.id == approval.indent_id).first()
    if not indent:
        raise HTTPException(status_code=404, detail="Indent not found")

    chosen_quote = db.query(MaterialQuotation).filter(MaterialQuotation.id == approval.selected_quotation_id).first()
    if not chosen_quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    chosen_quote.is_approved = True
    indent.status = "Approved"
    
    db.commit()
    return {"message": f"Approved vendor {chosen_quote.vendor_name} for {indent.item_name}"}