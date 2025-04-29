from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import mysql.connector
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    # "port": os.getenv("DB_PORT"),
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
@limiter.limit("100/10minute")  # Limit to 3 requests per 10 minutes
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/submit-rsvp")
@limiter.limit("20/10minute")  # Limit to 3 requests per 10 minutes
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

def get_rsvps():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all RSVPs
        cursor.execute("""
            SELECT guest_name, response, is_main_guest, created_at 
            FROM rsvps 
            ORDER BY created_at DESC
        """)
        rsvps = cursor.fetchall()
        
        # Separate attending and not attending
        attending = [rsvp for rsvp in rsvps if rsvp['response'] == 'yes']
        not_attending = [rsvp for rsvp in rsvps if rsvp['response'] == 'no']
        
        return {
            'attending': attending,
            'not_attending': not_attending,
            'attending_count': len(attending),
            'not_attending_count': len(not_attending)
        }
    
    finally:
        cursor.close()
        conn.close()

@app.get("/rsvp-list", response_class=HTMLResponse)
@limiter.limit("100/10minute")  # Limit to 3 requests per 10 minutes
async def rsvp_list(request: Request):
    rsvps = get_rsvps()
    return templates.TemplateResponse(
        "rsvp_list.html",
        {
            "request": request,
            "attending": rsvps['attending'],
            "not_attending": rsvps['not_attending'],
            "attending_count": rsvps['attending_count'],
            "not_attending_count": rsvps['not_attending_count']
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=44018)