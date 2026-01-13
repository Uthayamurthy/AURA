from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.api import deps

router = APIRouter()

@router.post("/login/access-token", response_model=schemas.token.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Supports:
    - Admin: username (username field)
    - Professor: email (username field)
    """
    # 1. Try Admin
    admin = db.query(models.Admin).filter(models.Admin.username == form_data.username).first()
    user = None
    role = None
    
    if admin and security.verify_password(form_data.password, admin.password_hash):
        user = admin
        role = "admin"
    else:
        # 2. Try Professor (Case Insensitive)
        prof = db.query(models.Professor).filter(func.lower(models.Professor.email) == form_data.username.lower()).first()
        if prof and security.verify_password(form_data.password, prof.password_hash):
            user = prof
            role = "professor"
        else:
            # 3. Try Student (Case Insensitive)
            student = db.query(models.Student).filter(func.lower(models.Student.email) == form_data.username.lower()).first()
            if student and security.verify_password(form_data.password, student.password_hash):
                user = student
                role = "student"

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email/username or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Subject format: "role:id"
    subject = f"{role}:{user.id}"
    
    return {
        "access_token": security.create_access_token(
            subject=subject, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
