from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema para criação de usuário (registro)"""
    name: str = Field(..., min_length=2, max_length=100, description="Nome completo")
    email: EmailStr = Field(..., description="Email válido")
    password: str = Field(..., min_length=6, description="Senha mínimo 6 caracteres")
    security_word: str = Field(..., min_length=3, max_length=50, description="Palavra de segurança para recuperação")

class UserLogin(BaseModel):
    """Schema para login - Agora aceita email ou nome de usuário"""
    identifier: str = Field(..., description="Email ou nome de usuário")
    password: str = Field(..., description="Senha do usuário")

class UserOut(BaseModel):
    """Schema para retorno de dados do usuário (sem senha)"""
    user_id: str
    name: str
    email: str
    created_at: datetime

class PasswordReset(BaseModel):
    """Schema para recuperação de senha"""
    email: EmailStr = Field(..., description="Email cadastrado")
    security_word: str = Field(..., description="Palavra de segurança")
    new_password: str = Field(..., min_length=6, description="Nova senha")

class PasswordUpdate(BaseModel):
    """Schema para atualização de senha (quando logado)"""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=6, description="Nova senha")

class Token(BaseModel):
    """Schema para resposta de login"""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOut

class RefreshTokenResponse(BaseModel):
    """Schema para resposta do refresh"""
    access_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    """Schema para a requisição de refresh"""
    refresh_token: str

class DeviceToken(BaseModel):
    """Schema para registro de token do dispositivo"""
    device_token: str = Field(..., description="Token FCM do dispositivo")
    platform: Optional[str] = Field(default="android", description="Plataforma (android/ios)")

class EmailOnly(BaseModel):
    """Schema para endpoints que precisam só do email"""
    email: EmailStr

class SecurityWordCheck(BaseModel):
    """Schema para validar palavra de segurança"""
    email: EmailStr
    security_word: str