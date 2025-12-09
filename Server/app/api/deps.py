from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app import models
from app.schemas import token as token_schema

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login" # We will define this endpoint
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> models.Admin | models.Professor:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = token_schema.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    if not token_data.sub:
         raise HTTPException(status_code=404, detail="User not found")

    # Format: "role:id"
    try:
        role, user_id = token_data.sub.split(":")
    except ValueError:
         raise HTTPException(status_code=403, detail="Invalid token subject format")

    if role == "admin":
        user = db.query(models.Admin).filter(models.Admin.id == int(user_id)).first()
    elif role == "professor":
        user = db.query(models.Professor).filter(models.Professor.id == int(user_id)).first()
    elif role == "student":
        user = db.query(models.Student).filter(models.Student.id == int(user_id)).first()
    else:
        raise HTTPException(status_code=403, detail="Invalid user role")
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

def get_current_active_admin(
    current_user: models.Admin | models.Professor = Depends(get_current_user),
) -> models.Admin:
    if not isinstance(current_user, models.Admin):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_active_professor(
    current_user: models.Admin | models.Professor = Depends(get_current_user),
) -> models.Professor:
    if not isinstance(current_user, models.Professor):
         raise HTTPException(
            status_code=400, detail="The user is not a professor"
        )
    return current_user

def get_current_active_student(
    current_user: models.Admin | models.Professor | models.Student = Depends(get_current_user),
) -> models.Student:
    if not isinstance(current_user, models.Student):
         raise HTTPException(
            status_code=400, detail="The user is not a student"
        )
    return current_user