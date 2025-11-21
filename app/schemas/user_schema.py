from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: constr(min_length=6)
    security_word: str

class UserLogin(BaseModel):
    identifier: str
    password: str

class PasswordReset(BaseModel):
    email: EmailStr
    security_word: str
    new_password: constr(min_length=6)

class EmailOnly(BaseModel):
    email: EmailStr

class SecurityWordCheck(BaseModel):
    email: EmailStr
    security_word: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

class DeviceToken(BaseModel):
    device_token: str
    platform: Optional[str] = "android"

# 🟢 ATUALIZADO: Removido o campo recurrence
class ExamSchedule(BaseModel):
    exam_name: str
    exam_date: str