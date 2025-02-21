from datetime import date
from io import BytesIO
from typing import Dict, List, Optional

import mysql.connector
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mysql@123",
            database="timetable"
        )
    except mysql.connector.Error as e:
        print("Error connecting to MySQL:", e)
        return None

@app.get("/")
def home():
    return {"message": "Welcome to the Timetable API"}

# ---------------- Instructor CRUD Operations ----------------
class Instructor(BaseModel):
    id_number: str
    name: str
    dept: str

@app.post("/upload")
async def upload_instructors(file: UploadFile = File(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None  # ✅ Initialize cursor before try block
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # ✅ Ensure required columns exist
        required_columns = {"id_number", "instructor_name", "dept"}
        if not required_columns.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Missing required columns: {required_columns - set(df.columns)}")

        # ✅ Clean data: Drop rows where any required column is missing
        df.dropna(subset=["id_number", "instructor_name", "dept"], inplace=True)

        # ✅ Trim whitespace from department names
        df["dept"] = df["dept"].astype(str).str.strip()

        # ✅ Fetch existing departments from DB
        cursor = conn.cursor()  # ✅ Cursor is now guaranteed to be assigned
        cursor.execute("SELECT dept_name FROM Department")
        existing_departments = {row[0] for row in cursor.fetchall()}

        # ✅ Identify missing departments
        missing_departments = set(df["dept"]) - existing_departments
        if missing_departments:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot insert instructors. The following departments do not exist: {', '.join(missing_departments)}. Please add them first."
            )

        # ✅ Insert instructors
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO Instructor (instructor_name,id_number, dept) VALUES (%s, %s, %s)",
                (row["instructor_name"], row["id_number"], row["dept"])
            )

        conn.commit()
        return {"message": "Instructors uploaded successfully"}

    except mysql.connector.Error as e:
        if cursor:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        if cursor:
            cursor.close()  # ✅ Cursor will only be closed if it was assigned
        conn.close()



@app.get("/instructor", response_model=List[Instructor])
def get_instructors():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_number, instructor_name as name, dept FROM Instructor")
        instructors = cursor.fetchall()
        return instructors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching instructors: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/instructor")
def add_instructor(instructor: Instructor):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Instructor (id_number, instructor_name, dept) VALUES (%s, %s, %s)",
            (instructor.id_number, instructor.name, instructor.dept)
        )
        conn.commit()
        return {"message": "Instructor added successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding instructor: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/instructor/{id_number}")
def update_instructor(id_number: str, instructor: Instructor):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Instructor SET instructor_name = %s, dept = %s WHERE id_number = %s",
            (instructor.name, instructor.dept, id_number)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Instructor not found")
        return {"message": "Instructor updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating instructor: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/instructor/{id_number}")
def delete_instructor(id_number: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Instructor WHERE id_number = %s", (id_number,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Instructor not found")
        return {"message": "Instructor deleted successfully"}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
# ---------------- File Upload & Excel Processing ----------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), dtype=str)

        # ✅ Strip spaces from column names
        df.columns = df.columns.str.strip()

        # ✅ Rename columns (if necessary)
        column_mapping = {"NAME": "INSTRUCTOR_NAME"}
        df.rename(columns=column_mapping, inplace=True)

        # ✅ Check required columns
        required_columns = ['Id_NUMBER', 'INSTRUCTOR_NAME', 'DEPT']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Invalid file format. Found columns: {df.columns.tolist()}")

        # ✅ Remove duplicate Id_NUMBERs within the file
        df.drop_duplicates(subset=['Id_NUMBER'], inplace=True)

        conn = get_db_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")

        cursor = conn.cursor()

        # ✅ Get all valid department names from the Department table
        cursor.execute("SELECT dept_name FROM Department")
        valid_departments = {dept[0].strip().lower() for dept in cursor.fetchall()}  # Convert to lowercase set

        # ✅ Filter out instructors with invalid departments
        valid_rows = []
        invalid_departments = set()
        for _, row in df.iterrows():
            dept_name = row['DEPT'].strip().lower()  # Normalize department names
            if dept_name in valid_departments:
                valid_rows.append((row['Id_NUMBER'], row['INSTRUCTOR_NAME'], row['DEPT']))
            else:
                invalid_departments.add(row['DEPT'])

        if invalid_departments:
            print(f"❌ Skipping instructors with invalid departments: {invalid_departments}")

        # ✅ Insert valid instructors
        for id_number, name, dept in valid_rows:
            try:
                cursor.execute(
                    """
                    INSERT INTO Instructor (Id_NUMBER, INSTRUCTOR_NAME, DEPT)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    INSTRUCTOR_NAME = VALUES(INSTRUCTOR_NAME), 
                    DEPT = VALUES(DEPT)
                    """,
                    (id_number, name, dept)
                )
            except mysql.connector.Error as e:
                print(f"MySQL Error inserting instructor '{id_number}':", e)
                raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

        conn.commit()
        return {"message": "File uploaded. Invalid departments skipped."}

    except Exception as e:
        print("Error processing file:", str(e))  # ✅ Print full error for debugging
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        cursor.close()
        conn.close()


# ✅ Fetch Departments API
@app.get("/departments", response_model=List[Dict[str, str]])
def get_departments():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT dept_name FROM Department")
        departments = cursor.fetchall()
        return [{"dept_name": dept[0]} for dept in departments]
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ Add Department API
@app.post("/departments")
async def add_department(dept: Dict[str, str]):
    dept_name = dept.get("dept_name")
    if not dept_name:
        raise HTTPException(status_code=400, detail="Department name is required")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Department (dept_name) VALUES (%s) ON DUPLICATE KEY UPDATE dept_name=dept_name",
            (dept_name,)
        )
        conn.commit()
        return {"message": "Department added successfully"}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ Update Department API
@app.put("/departments/{dept_name}")
async def update_department(dept_name: str, dept: Dict[str, str]):
    new_dept_name = dept.get("dept_name")
    if not new_dept_name:
        raise HTTPException(status_code=400, detail="New department name is required")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Department SET dept_name=%s WHERE dept_name=%s", (new_dept_name, dept_name))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Department not found")
        return {"message": "Department updated successfully"}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ Delete Department API
@app.delete("/departments/{dept_name}")
async def delete_department(dept_name: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Department WHERE dept_name=%s", (dept_name,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Department not found")
        return {"message": "Department deleted successfully"}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ Upload Excel File & Insert Departments
@app.post("/upload_departments")
async def upload_departments(file: UploadFile = File(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        contents = await file.read()  # Read file as bytes
        df = pd.read_excel(BytesIO(contents))  # Convert bytes to file-like object

        # ✅ Check if 'dept_name' column exists
        if "dept_name" not in df.columns:
            raise HTTPException(status_code=400, detail="Invalid file format. Column 'dept_name' is required.")

        # ✅ Drop NaN values and strip extra spaces
        df["dept_name"] = df["dept_name"].astype(str).str.strip()  # Convert to string & strip spaces
        df = df[df["dept_name"].notna() & (df["dept_name"] != "")]  # Remove empty values

        if df.empty:
            raise HTTPException(status_code=400, detail="No valid department names found in the file.")

        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO Department (dept_name) VALUES (%s) ON DUPLICATE KEY UPDATE dept_name=dept_name",
                (row["dept_name"],)
            )
        conn.commit()
        return {"message": "Departments uploaded successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()

# ---------------- Subject CRUD Operations ----------------
class Subject(BaseModel):
    subject_name: str

@app.post("/upload_subjects")
async def upload_subjects(file: UploadFile = File(...)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # Ensure required column exists
        if "subject_name" not in df.columns:
            raise HTTPException(status_code=400, detail="Missing required column: subject_name")

        # Clean data: Drop rows where subject_name is missing
        df.dropna(subset=["subject_name"], inplace=True)

        cursor = conn.cursor()

        # Insert subjects
        for _, row in df.iterrows():
            cursor.execute(
                "INSERT INTO Subject (subject_name) VALUES (%s) ON DUPLICATE KEY UPDATE subject_name=subject_name",
                (row["subject_name"],)
            )

        conn.commit()
        return {"message": "Subjects uploaded successfully"}

    except mysql.connector.Error as e:
        if cursor:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.get("/subjects", response_model=List[Subject])
def get_subjects():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT subject_name FROM Subject")
        subjects = cursor.fetchall()
        return subjects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subjects: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/subjects")
def add_subject(subject: Subject):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Subject (subject_name) VALUES (%s)",
            (subject.subject_name,)
        )
        conn.commit()
        return {"message": "Subject added successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding subject: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/subjects/{subject_name}")
def delete_subject(subject_name: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Subject WHERE subject_name = %s", (subject_name,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subject not found")
        return {"message": "Subject deleted successfully"}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/subjects/{subject_name}")
async def update_subject(subject_name: str, subject: Subject):
    new_subject_name = subject.subject_name

    if not new_subject_name:
        raise HTTPException(status_code=400, detail="New subject name is required")

    if new_subject_name == subject_name:
        raise HTTPException(status_code=400, detail="New subject name must be different from the old one")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Check if the subject exists
        cursor.execute("SELECT 1 FROM Subject WHERE subject_name = %s", (subject_name,))
        existing_subject = cursor.fetchone()

        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Update subject name
        cursor.execute(
            "UPDATE Subject SET subject_name = %s WHERE subject_name = %s",
            (new_subject_name, subject_name)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=400, detail="No changes made. Subject name may be the same.")

        return {"message": "Subject updated successfully"}

    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")

    finally:
        cursor.close()
        conn.close()


# ✅ Availability Model
# Availability Model
class InstructorAvailability(BaseModel):
    instructor_name: str
    start_date: date
    status: str

@app.get("/availability/{instructor_name}")
def get_availability(instructor_name: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Availability WHERE instructor_name = %s", (instructor_name,))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return records

@app.post("/availability")
def add_availability(availability: InstructorAvailability):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Availability (instructor_name, start_date, status) VALUES (%s, %s, %s)",
        (availability.instructor_name, availability.start_date, availability.status)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Availability added successfully"}

@app.put("/availability/{instructor_name}/{start_date}")
def update_availability(instructor_name: str, start_date: date, status_update: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Availability SET status = %s WHERE instructor_name = %s AND start_date = %s",
        (status_update["status"], instructor_name, start_date)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Availability updated successfully"}

@app.delete("/availability/{instructor_name}/{start_date}")
def delete_availability(instructor_name: str, start_date: date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Availability WHERE instructor_name = %s AND start_date = %s", (instructor_name, start_date))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Availability deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
