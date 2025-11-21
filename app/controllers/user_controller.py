from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user_schema import UserCreate, UserLogin, PasswordReset, Token, EmailOnly, SecurityWordCheck, DeviceToken, ExamSchedule
from app.services.user_service import user_service
from app.utils.auth import AuthUtils, get_current_user
from app.firebase_setup import schedule_reminder 

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    return await user_service.register_user(user_data)

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    return await user_service.login_user(login_data)

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    return await user_service.reset_password(reset_data)

@router.post("/check-email")
async def check_email(email_data: EmailOnly):
    user = await user_service._get_user_by_email(email_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email não encontrado")
    return {"message": "Email encontrado", "exists": True}

@router.post("/verify-security-word")
async def verify_security_word(data: SecurityWordCheck):
    user = await user_service._get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email não encontrado")
    if user.get("security_word") != data.security_word.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Palavra de segurança incorreta")
    return {"message": "Palavra de segurança correta", "valid": True}

@router.post("/device-token", status_code=status.HTTP_200_OK) 
async def register_device_token(
    data: DeviceToken,
    current_user_id: str = Depends(get_current_user)
):
    await user_service.save_device_token(current_user_id, data.device_token, data.platform)
    return {"message": "Token do dispositivo registrado com sucesso"}

@router.post("/schedule-exam-test", status_code=status.HTTP_200_OK) 
async def schedule_exam_test(
    exam_data: ExamSchedule, 
    current_user_id: str = Depends(get_current_user)
):
    """
    Agendar um lembrete de exame simples.
    """
    user = await user_service.get_user_by_id(current_user_id, include_sensitive=True) 
    
    if not user or not user.get('device_tokens'):
        raise HTTPException(status_code=404, detail="Token do dispositivo não encontrado.")
    
    latest_token = user['device_tokens'][-1]['token'] 
    
    # 🟢 ATUALIZADO: Chama sem recurrence
    schedule_reminder(
        current_user_id,
        latest_token,
        exam_data.exam_name, 
        exam_data.exam_date
    )
    
    return {"message": "Agendamento realizado com sucesso."}

@router.get("/me")
async def get_current_user_info(current_user_id: str = Depends(get_current_user)):
    user = await user_service.get_user_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return user