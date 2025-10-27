from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user_schema import UserCreate, UserLogin, PasswordReset, Token, EmailOnly, SecurityWordCheck
from app.services.user_service import user_service
from app.utils.auth import AuthUtils, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Registrar novo usuário"""
    return await user_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Fazer login"""
    return await user_service.login_user(login_data)


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Recuperar senha com palavra de segurança"""
    return await user_service.reset_password(reset_data)


@router.post("/check-email")
async def check_email(email_data: EmailOnly):
    """Verificar se email existe (para recuperação)"""
    user = await user_service._get_user_by_email(email_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado"
        )
    return {"message": "Email encontrado", "exists": True}


@router.post("/verify-security-word")
async def verify_security_word(data: SecurityWordCheck):
    """Verificar palavra de segurança"""
    user = await user_service._get_user_by_email(data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado"
        )

    if user.get("security_word") != data.security_word.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Palavra de segurança incorreta"
        )

    return {"message": "Palavra de segurança correta", "valid": True}


@router.get("/me")
async def get_current_user_info(current_user_id: str = Depends(get_current_user)):
    """Obter dados do usuário logado"""
    user = await user_service.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return user


@router.get("/test-protected")
async def test_protected_route(current_user_id: str = Depends(get_current_user)):
    """Rota de teste para verificar autenticação"""
    return {
        "message": "Rota protegida funcionando!",
        "user_id": current_user_id,
        "authenticated": True
    }