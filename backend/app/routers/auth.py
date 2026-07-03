from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import verify_password, create_access_token
from app.deps import get_db, get_current_admin
from app.models import AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = crud.get_admin_by_username(db, form_data.username)
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(subject=admin.username)
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.AdminOut)
def me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin
