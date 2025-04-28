from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import mysql.connector
from dotenv import load_dotenv
import os
from typing import List

# Load environment variables
load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Create RSVP table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rsvps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            guest_name VARCHAR(255) NOT NULL,
            response VARCHAR(10) NOT NULL,
            is_main_guest BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/submit-rsvp")
async def submit_rsvp(
    request: Request,
    guest_name: str = Form(...),
    response: str = Form(...)
):
    form_data = await request.form()
    additional_guests = form_data.getlist("additional_guests")
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Insert main guest
        cursor.execute(
            "INSERT INTO rsvps (guest_name, response, is_main_guest) VALUES (%s, %s, %s)",
            (guest_name, response, True)
        )
        
        # Insert additional guests if any
        if additional_guests:
            for guest in additional_guests:
                if guest.strip():  # Only insert non-empty guest names
                    cursor.execute(
                        "INSERT INTO rsvps (guest_name, response, is_main_guest) VALUES (%s, %s, %s)",
                        (guest, response, False)
                    )
        
        conn.commit()
        return {"message": "RSVP submitted successfully"}
    
    except Exception as e:
        conn.rollback()
        raise e
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=44018)