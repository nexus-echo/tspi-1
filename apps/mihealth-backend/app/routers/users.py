"""Admin user management: create doctor/admin accounts, list users."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import Role, User
from app.schemas import AdminCreateUser, UserOut
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: AdminCreateUser,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
) -> User:
    if body.role == Role.patient:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Patients self-register via /auth/register")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()
