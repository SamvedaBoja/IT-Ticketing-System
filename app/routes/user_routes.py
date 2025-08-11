from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from app.models.user import User, UserCreate, UserRead, UserRole
from app.database.config import get_session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead, status_code=201)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Pre-check for existing username or email
    existing = session.exec(
        select(User).where((User.username == user.username) | (User.email == user.email))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Department assignment logic
    if user.role == UserRole.agent:
        if not user.department:
            raise HTTPException(status_code=400, detail="Agents must have a department")
    elif user.role == UserRole.triage_officer:
        user.department = user.department or "All"
    elif user.role == UserRole.employee:
        user.department = user.department or "N/A"

    db_user = User.from_orm(user)
    session.add(db_user)
    try:
        session.commit()
        session.refresh(db_user)
    except IntegrityError:
        session.rollback()
        # This handles potential race condition where another process inserted same user at the same time
        raise HTTPException(status_code=400, detail="Username or email already exists")
    return db_user

@router.get("/", response_model=list[UserRead])
def get_users(
    x_user_id: int = Header(..., alias="X-User-ID"),
    session: Session = Depends(get_session)
):
    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role not in ["triage_officer", "agent"]:
        raise HTTPException(status_code=403, detail="Access denied")

    users = session.exec(select(User)).all()
    return users

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    x_user_id: int = Header(..., alias="X-User-ID"),
    session: Session = Depends(get_session)
):
    # Fetch the requesting user
    requesting_user = session.get(User, x_user_id)
    if not requesting_user:
        raise HTTPException(status_code=404, detail="Requesting user not found")

    # Employees can only see their own record
    if requesting_user.role == "employee" and requesting_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch the target user
    target_user = session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return target_user