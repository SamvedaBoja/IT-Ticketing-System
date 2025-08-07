from fastapi import FastAPI
from app.database.config import create_db_and_tables
from app.routes import user_routes
from app.routes.ticket_routes import router as ticket_router

app = FastAPI()

app.include_router(user_routes.router)
app.include_router(ticket_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"message": "Ticketing System API is up!"}