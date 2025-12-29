from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Float, Date
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import Optional, List  # <--- Added this to fix the error
import os
import shutil
import uuid

# ==========================================
import os  # Make sure this is imported at the top if not already there

# ===============================================
import os  # <--- MAKE SURE YOU ADD THIS AT THE VERY TOP OF THE FILE

# ... keep your other imports (FastAPI, sqlalchemy, etc.) ...

# ===============================================
# 1. DATABASE CONFIGURATION (Updated for Render)
# ===============================================

# Get the Database URL from Render. If it's empty, use your local file.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sitetrack.db")

# Fix the URL format (Render uses 'postgres://' but Python needs 'postgresql://')
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the Engine
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    # Settings for SQLite (Local Laptop)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Settings for PostgreSQL (Render Cloud)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# ==========================================
# 2. DATABASE MODELS (The Tables)
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
    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    location = Column(String)

class DWREntry(Base):
    __tablename__ = "dwr_entries"
    entry_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    user_name = Column(String)
    description = Column(String)
    location_work = Column(String)
    quantity = Column(String)
    subcontractor = Column(String)
    site_incharge = Column(String)
    remarks = Column(String)
    entry_date = Column(Date, default=date.today)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. PYDANTIC SCHEMAS (Data Validation)
# ==========================================

# Schema for Login
class LoginRequest(BaseModel):
    phone_number: str
    password: str
# Add this class near your other class definitions
class ProjectCreate(BaseModel):
    project_name: str
    location: str
    manager_id: int  # We will send the user ID as an integer
# Schema for creating/updating a DWR
class DWRItem(BaseModel):
    project_id: Optional[int] = None
    user_name: str
    description: str
    location_work: str
    quantity: str
    subcontractor: str
    site_incharge: str
    remarks: str

# ==========================================
# 4. FASTAPI APP & DEPENDENCY
# ==========================================

app = FastAPI()

# Dependency to get the database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 5. API ROUTES
# ==========================================

@app.get("/")
def home():
    return {"message": "SiteTrack Server is Running!"}

# --- REPLACE YOUR EXISTING LOGIN FUNCTION WITH THIS ---
@app.post("/login")
def login(user_req: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login Attempt: Phone={user_req.phone_number}, Pass={user_req.password}") # DEBUG PRINT

    # 1. Check if phone exists AT ALL (ignoring password)
    user_by_phone = db.query(User).filter(User.phone_number == user_req.phone_number).first()
    
    if not user_by_phone:
        print("❌ Error: Phone number not found in DB")
        raise HTTPException(status_code=401, detail="Phone number not registered")

    # 2. Check Password
    print(f"✅ Found User: {user_by_phone.name}, DB Password: '{user_by_phone.password}'")
    
    if user_by_phone.password != user_req.password:
        print("❌ Error: Password mismatch")
        raise HTTPException(status_code=401, detail="Wrong Password")

    # 3. Success
    print("🎉 Login Successful!")
    return {
        "status": "success",
        "message": "Login successful",
        "user_id": user_by_phone.id,
        "id": user_by_phone.id,
        "userId": str(user_by_phone.id),
        "name": user_by_phone.name,
        "role": user_by_phone.role,  # <--- IMPORTANT: Sending Role to Flutter
        "token": "fake_token_123"
    }
# --- PASTE THIS NEW CODE ---

class UserCreate(BaseModel):
    name: str
    phone_number: str
    password: str
    role: str = "admin"

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if phone number already exists
    existing_user = db.query(User).filter(User.phone_number == user.phone_number).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # 2. Create the new user
    new_user = User(
        name=user.name,
        phone_number=user.phone_number,
        password=user.password,  
        role=user.role
    )
    
    # 3. Save to Database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully!", "user_id": new_user.id}
# --- START OF NEW PROJECT CODE ---

# 1. Define what data we need to create a project
class ProjectCreate(BaseModel):
    project_name: str
    location: str

# 2. Create the API Endpoint
@app.post("/create_project")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Create the new project variable
    new_project = Project(
        project_name=project.project_name,
        location=project.location
    )
    
    # Save it to the Cloud Database
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return {"message": "Project created successfully!", "project_id": new_project.project_id}

# --- END OF NEW PROJECT CODE ---
# --- END OF NEW CODE ---
# --- GET PROJECTS ---
# Note: Providing both /projects and /get_projects to ensure compatibility
@app.get("/projects")
def get_projects_v1(db: Session = Depends(get_db)):
    return db.query(Project).all()

@app.get("/get_projects")
def get_projects_v2(db: Session = Depends(get_db)):
    return db.query(Project).all()

# --- ADD DWR ENTRY ---
@app.post("/add-dwr")
def add_dwr(item: DWRItem, db: Session = Depends(get_db)):
    try:
        new_dwr = DWREntry(
            project_id=item.project_id,
            user_name=item.user_name,
            description=item.description,
            location_work=item.location_work,
            quantity=item.quantity,
            subcontractor=item.subcontractor,
            site_incharge=item.site_incharge,
            remarks=item.remarks,
            entry_date=date.today()
        )
        db.add(new_dwr)
        db.commit()
        db.refresh(new_dwr)
        return {"message": "DWR Saved Successfully", "id": new_dwr.entry_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
# --- 1. NEW DB MODEL FOR DPR ---
# --- 1. UPDATE THE DB MODEL (Place this with your other models) ---
class DPREntry(Base):
    __tablename__ = "dpr_entries"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    user_name = Column(String)
    user_role = Column(String)
    date = Column(String)
    description = Column(String)
    location = Column(String)
    
    # --- CHANGED: We replaced percent_work with these ---
    finished_qty = Column(String)
    planned_qty = Column(String)
    unit = Column(String)
    percentage_done = Column(String) 
    # --------------------------------------------------

    subcontractor = Column(String)
    site_engineer = Column(String)
    site_incharge = Column(String)
    reason_incompletion = Column(String)
class DPRItem(BaseModel):
    project_id: int
    user_name: str
    user_role: str
    date: str
    description: str
    location: str
    
    # --- CHANGED: This must match what Flutter sends ---
    finished_qty: str
    planned_qty: str
    unit: str
    percentage_done: str 
    # --------------------------------------------------

    subcontractor: str
    site_engineer: str
    site_incharge: str
    reason_incompletion: str
# --- GET DWR LIST ---
@app.get("/get-dwr/{project_id}")
def get_dwr(project_id: int, db: Session = Depends(get_db)):
    entries = db.query(DWREntry).filter(DWREntry.project_id == project_id).order_by(DWREntry.entry_id.desc()).all()
    
    # Format list for Flutter
    dwr_list = []
    for i, row in enumerate(entries):
        dwr_list.append({
            "sno": str(i + 1),
            "entry_id": row.entry_id, # Added ID so we can update/delete later
            "desc": row.description,
            "location": row.location_work,
            "quantity": row.quantity,
            "subcontractor": row.subcontractor,
            "engineer": row.user_name,
            "incharge": row.site_incharge,
            "remarks": row.remarks,
            "date": str(row.entry_date)
        })
    return dwr_list
# --- CREATE PROJECT ENDPOINT ---
@app.post("/projects") 
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Create the new project object
    new_project = Project(
        project_name=project.project_name,
        location=project.location,
        manager_id=project.manager_id,
        created_at=date.today() # Sets today's date automatically
    )
    
    # Save to Database
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project

# --- UPDATE DWR ---
@app.put("/update_dwr/{entry_id}")
def update_dwr(entry_id: int, item: DWRItem, db: Session = Depends(get_db)):
    dwr_entry = db.query(DWREntry).filter(DWREntry.entry_id == entry_id).first()
    
    if not dwr_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Update fields
    dwr_entry.user_name = item.user_name
    dwr_entry.description = item.description
    dwr_entry.location_work = item.location_work
    dwr_entry.quantity = item.quantity
    dwr_entry.subcontractor = item.subcontractor
    dwr_entry.site_incharge = item.site_incharge
    dwr_entry.remarks = item.remarks
    
    db.commit()
    return {"message": "DWR updated successfully"}

# --- DELETE DWR ---
@app.delete("/delete_dwr/{entry_id}")
def delete_dwr(entry_id: int, db: Session = Depends(get_db)):
    dwr_entry = db.query(DWREntry).filter(DWREntry.entry_id == entry_id).first()
    
    if not dwr_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
        
    db.delete(dwr_entry)
    db.commit()
    return {"message": "DWR deleted successfully"}

# ==========================================
# 6. SERVER STARTUP
# ==========================================

# --- IN main.py ---

# 1. Update the DPREntry Model to match your requirements
class DPREntry(BaseModel):
    project_id: int
    user_name: str
    date: str
    description: str
    location: str
    percent_work: str       # New Field
    subcontractor: str      # New Field
    site_engineer: str      # New Field
    site_incharge: str      # New Field
    reason_incompletion: str # New Field

# 2. Update the Create Table SQL (If you run this on a fresh database, or just add columns manually)
# For now, let's assume we just store the new data.

# 3. Update the Add DPR Endpoint
@app.post("/add-dpr")
def add_dpr(entry: DPREntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We will create a table if it doesn't exist with the new columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dpr_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_name TEXT,
            date TEXT,
            description TEXT,
            location TEXT,
            percent_work TEXT,
            subcontractor TEXT,
            site_engineer TEXT,
            site_incharge TEXT,
            reason_incompletion TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO dpr_entries (
            project_id, user_name, date, description, location, 
            percent_work, subcontractor, site_engineer, site_incharge, reason_incompletion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry.project_id, entry.user_name, entry.date, entry.description, entry.location,
        entry.percent_work, entry.subcontractor, entry.site_engineer, 
        entry.site_incharge, entry.reason_incompletion
    ))
    
    conn.commit()
    conn.close()
    return {"message": "DPR Entry added successfully"}

# 4. Update the Get DPR Endpoint
# Replace your old get_dpr function with this one
@app.get("/get-dpr/{project_id}")
def get_dpr(project_id: int, db: Session = Depends(get_db)):
    # Query the database using the new SQLAlchemy session
    dprs = db.query(DPREntry).filter(DPREntry.project_id == project_id).all()
    
    if not dprs:
        # Return an empty list instead of a 404 error so the app doesn't crash
        return []
    
    return dprs
    # Ensure table exists so we don't crash on first load
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dpr_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_name TEXT,
            date TEXT,
            description TEXT,
            location TEXT,
            percent_work TEXT,
            subcontractor TEXT,
            site_engineer TEXT,
            site_incharge TEXT,
            reason_incompletion TEXT
        )
    ''')
    
    cursor.execute("SELECT * FROM dpr_entries WHERE project_id = ?", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Convert database rows to a list of dictionaries
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "project_id": row[1],
            "user_name": row[2],
            "date": row[3],
            "description": row[4],
            "location": row[5],
            "percent_work": row[6],
            "subcontractor": row[7],
            "site_engineer": row[8],
            "site_incharge": row[9],
            "reason_incompletion": row[10]
        })
    return results
from fastapi import FastAPI, HTTPException # Import HTTPException
from pydantic import BaseModel
# ... (rest of your imports)

# 1. Update the Model to accept 'user_role'
class DPREntry(BaseModel):
    project_id: int
    user_name: str
    user_role: str          # <--- NEW: We need to know who is knocking!
    date: str
    description: str
    location: str
    percent_work: str
    subcontractor: str
    site_engineer: str
    site_incharge: str
    reason_incompletion: str

# 2. Update the Endpoint to CHECK permissions
@app.post("/add-dpr")
def add_dpr(entry: DPREntry):
    # --- SECURITY CHECK ---
    # Define who is allowed to CREATE a DPR
    allowed_roles = ["Admin", "MD", "Site Engineer", "Site In-charge"]
    
    if entry.user_role not in allowed_roles:
        # If role is Sales or QMS, kick them out!
        raise HTTPException(status_code=403, detail="Access Denied: You do not have permission to create DPRs.")
    # ----------------------

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # (Ensure table has columns, same as before...)
    
    cursor.execute('''
        INSERT INTO dpr_entries (
            project_id, user_name, date, description, location, 
            percent_work, subcontractor, site_engineer, site_incharge, reason_incompletion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry.project_id, entry.user_name, entry.date, entry.description, entry.location,
        entry.percent_work, entry.subcontractor, entry.site_engineer, 
        entry.site_incharge, entry.reason_incompletion
    ))
    
    conn.commit()
    conn.close()
    return {"message": "DPR Entry added successfully"}
# --- ADD DPR ENTRY ---
@app.post("/add-dpr")
def add_dpr(item: DPRItem, db: Session = Depends(get_db)):
    try:
        new_dpr = DPREntry(
            project_id=item.project_id,
            user_name=item.user_name,
            user_role=item.user_role,
            date=item.date,
            description=item.description,
            location=item.location,
            
            # --- MAPPING NEW FIELDS ---
            finished_qty=item.finished_qty,
            planned_qty=item.planned_qty,
            unit=item.unit,
            percentage_done=item.percentage_done,
            # --------------------------
            
            subcontractor=item.subcontractor,
            site_engineer=item.site_engineer,
            site_incharge=item.site_incharge,
            reason_incompletion=item.reason_incompletion
        )
        db.add(new_dpr)
        db.commit()
        db.refresh(new_dpr)
        return {"message": "DPR Saved Successfully"}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    # ==========================================
# FEATURE 2: MATERIAL INDENT SYSTEM
# ==========================================

# --- 1. Database Model ---
class MaterialIndent(Base):
    __tablename__ = "material_indents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True) # Links to the Project
    item_name = Column(String)               # e.g., "Cement"
    quantity = Column(String)                # e.g., "50 bags"
    priority = Column(String)                # "High", "Medium", "Low"
    status = Column(String, default="Pending") # Pending -> Quoted -> Approved
    requested_by = Column(String)            # Name of Site Engineer
    date = Column(String)                    # e.g., "2023-10-27"

# --- 2. Pydantic Schema (What the App sends) ---
class IndentCreate(BaseModel):
    project_id: int
    item_name: str
    quantity: str
    priority: str = "Medium"
    requested_by: str
    date: str

# --- 3. API Endpoints ---

# A. Create a Request (For Site Engineers)
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

# B. Get All Indents for a Project (For Sales Team/MD)
@app.get("/get_indents/{project_id}")
def get_indents(project_id: int, db: Session = Depends(get_db)):
    indents = db.query(MaterialIndent).filter(MaterialIndent.project_id == project_id).all()
    if not indents:
        return [] # Return empty list if no requests
    return indents
# =======================================================
# FEATURE 2 COMPLETE: MATERIAL INDENT, QUOTES & APPROVAL
# =======================================================

# --- 1. Database Models ---

# (Make sure you have the MaterialIndent model from the previous step here.
# If you didn't paste it yet, paste it now. If you did, just add these new ones below it.)

class MaterialQuotation(Base):
    __tablename__ = "material_quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    indent_id = Column(Integer, index=True)  # Links to the Indent Request
    vendor_name = Column(String)
    price = Column(Float)
    is_approved = Column(Boolean, default=False)

# --- 2. Pydantic Schemas (Input Data) ---

class QuotationCreate(BaseModel):
    indent_id: int
    vendor_name: str
    price: float

class ApprovalUpdate(BaseModel):
    indent_id: int
    selected_quotation_id: int

# --- 3. API Endpoints ---

# A. Sales Team: Upload a Quote for a specific Indent
@app.post("/add_quotation")
def add_quotation(quote: QuotationCreate, db: Session = Depends(get_db)):
    # 1. Check if Indent exists
    indent = db.query(MaterialIndent).filter(MaterialIndent.id == quote.indent_id).first()
    if not indent:
        raise HTTPException(status_code=404, detail="Indent ID not found")
    
    # 2. Add the Quote
    new_quote = MaterialQuotation(
        indent_id=quote.indent_id,
        vendor_name=quote.vendor_name,
        price=quote.price
    )
    
    # 3. Update Indent status to "Quoted"
    indent.status = "Quoted"
    
    db.add(new_quote)
    db.commit()
    return {"message": "Quotation added successfully"}

# B. Sales Team: See all quotes for a specific Indent
@app.get("/get_quotes/{indent_id}")
def get_quotes(indent_id: int, db: Session = Depends(get_db)):
    quotes = db.query(MaterialQuotation).filter(MaterialQuotation.indent_id == indent_id).all()
    return quotes

# C. MD: Approve a Quote
@app.post("/approve_indent")
def approve_indent(approval: ApprovalUpdate, db: Session = Depends(get_db)):
    # 1. Get the Indent
    indent = db.query(MaterialIndent).filter(MaterialIndent.id == approval.indent_id).first()
    if not indent:
        raise HTTPException(status_code=404, detail="Indent not found")

    # 2. Get the specific Quote the MD chose
    chosen_quote = db.query(MaterialQuotation).filter(MaterialQuotation.id == approval.selected_quotation_id).first()
    if not chosen_quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    # 3. Mark Quote as Approved
    chosen_quote.is_approved = True
    
    # 4. Mark Indent as Final Approved
    indent.status = "Approved"
    
    db.commit()
    return {"message": f"Approved vendor {chosen_quote.vendor_name} for {indent.item_name}"}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)