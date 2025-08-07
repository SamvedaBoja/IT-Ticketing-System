from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from app.models.user import User, UserCreate, UserRead
from app.database.config import get_session

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
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
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user