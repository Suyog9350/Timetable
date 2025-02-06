from io import BytesIO
from typing import List

import mysql.connector
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Enable CORS
# Allow your frontend React app URL for local development (e.g., http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust with your frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",        # Replace with your MySQL username
            password="Mysql@123",  # Replace with your MySQL password
            database="timetable"   # Replace with your actual database name
        )
        return connection
    except mysql.connector.Error as e:
        print("Error connecting to MySQL:", e)
        return None

@app.get("/")
def home():
    return {"message": "Welcome to the Timetable API"}

# ---------------- Instructor CRUD Operations ----------------

# Model for instructor response
class Instructor(BaseModel):
    id_number: str  # Using string for VARCHAR compatibility
    name: str
    dept: str

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
        file_size = len(await file.read())
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")
        
        await file.seek(0)
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), dtype=str)
        
        df.columns = df.columns.str.strip()  # Remove extra spaces

        # Check and rename columns dynamically
        column_mapping = {
            "NAME": "INSTRUCTOR_NAME"
        }
        df.rename(columns=column_mapping, inplace=True)

        # Expected columns after renaming
        required_columns = ['Id_NUMBER', 'INSTRUCTOR_NAME', 'DEPT']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Invalid Excel file format. Found columns: {df.columns.tolist()}")

        connection = get_db_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Database connection failed")

        cursor = connection.cursor()
        try:
            for _, row in df.iterrows():
                cursor.execute(
                    "INSERT INTO Instructor (Id_NUMBER, INSTRUCTOR_NAME, DEPT) VALUES (%s, %s, %s)",
                    (row['Id_NUMBER'], row['INSTRUCTOR_NAME'], row['DEPT'])
                )
            connection.commit()
            return JSONResponse(content={"message": "File uploaded and data inserted into MySQL successfully"}, status_code=200)

        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Error inserting data: {str(e)}")

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# Department model
class Department(BaseModel):
    dept_name: str  # Primary key

# Get all departments
@app.get("/departments", response_model=List[Department])
def get_departments():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT dept_name FROM Department")
        departments = cursor.fetchall()
        return departments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching departments: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Add a new department
@app.post("/departments")
def add_department(dept: Department):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Department (dept_name) VALUES (%s)", (dept.dept_name,))
        conn.commit()
        return {"message": "Department added successfully"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Department already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding department: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Update a department (change dept_name)
@app.put("/departments/{dept_name}")
def edit_department(dept_name: str, new_dept: Department):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Department SET dept_name = %s WHERE dept_name = %s", (new_dept.dept_name, dept_name))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Department not found")
        conn.commit()
        return {"message": "Department updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating department: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Delete a department
@app.delete("/departments/{dept_name}")
def delete_department(dept_name: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Department WHERE dept_name = %s", (dept_name,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Department not found")
        conn.commit()
        return {"message": "Department deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting department: {str(e)}")
    finally:
        cursor.close()
        conn.close()



# Run FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
