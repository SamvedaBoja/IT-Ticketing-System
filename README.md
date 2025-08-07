# IT Ticketing System API

A role-based IT support ticketing system built using **FastAPI** and **MySQL**, supporting employee ticket submissions, triage workflows, and agent resolution processes.

---

## Overview

This project is a backend API for managing IT support tickets within an organization. It supports three user roles:

- **Employee** – submits support tickets  
- **Agent** – works on assigned tickets  
- **Triage Officer** – reviews new tickets, sets priority, and assigns to teams/agents

Built with:
- FastAPI + SQLModel
- MySQL (local setup)
- Modular route structure
- Swagger UI for easy testing

---

##  Project Structure

```
ticketing-api/
├── app/
│   ├── database/
│   │   └── config.py
│   ├── models/
│   │   ├── ticket.py
│   │   └── user.py
│   ├── routes/
│   │   ├── ticket_routes.py
│   │   └── user_routes.py
│   └── __init__.py
├── main.py
├── .env
├── requirements.txt
└── README.md
```

---

## Setup & Running Locally

### 1. Clone the Repository
```bash
git clone https://github.com/SamvedaBoja/IT-Ticketing-System.git
cd ticketing-api
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root:

```env
DATABASE_URL=mysql+mysqlconnector://root:<your-password>@localhost:3306/<your-database-name>
```

> Make sure your MySQL database is created beforehand.

### 5. Initialize Tables
Ensure your database is empty, then auto-generate tables:

```python
# Option 1: Add this once in your main.py and run the app
from app.database.config import create_db_and_tables
create_db_and_tables()

# Option 2: Call it once from a Python script or terminal
```

### 6. Run the FastAPI App
```bash
uvicorn main:app --reload
```

Visit: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for Swagger UI.

---

## Role-Based Access Logic

- Every request includes a custom header:  
  `X-User-ID: <id>`

- On each endpoint:
  - User is fetched from DB using this ID
  - Role is validated before proceeding
  - If unauthorized → `403 Forbidden`

---

## API Endpoints (V1)

### User Management
- `POST /users` – Create a user  
- `GET /users` – List users (Agent & Triage only)  
- `GET /users/{user_id}` – Get specific user  

### Employee Actions
- `POST /tickets` – Submit ticket  
- `GET /tickets/my` – View own tickets  
- `PUT /tickets/{id}/reopen` – Reopen resolved ticket  
- `PUT /tickets/{id}/close` – Close resolved ticket  

### Triage Officer Actions
- `GET /tickets/pending-triage` – View 'new' tickets  
- `PUT /tickets/{id}/triage` – Set priority, team, (optional) assign agent  

### Agent Actions
- `GET /tickets` – View all tickets  
- `GET /tickets/{id}` – View specific ticket  
- `PUT /tickets/{id}/assign` – Assign ticket to self  
- `PUT /tickets/{id}/resolve` – Resolve a ticket  

---

## Features

- Clean RESTful routes with separation of concerns
- SQLModel-based ORM models with built-in validation
- Datetime fields for created, updated, resolved timestamps
- Easy-to-use Swagger UI for testing

---
