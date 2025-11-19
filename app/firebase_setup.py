import firebase_admin
from firebase_admin import credentials, messaging
import os
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio

# -----------------------------------------------------------
# Configuração
# -----------------------------------------------------------
# Certifique-se de que este arquivo JSON esteja na RAIZ do seu projeto backend!
SERVICE_ACCOUNT_FILE = 'firebase-service-account.json' 

# Inicializa o agendador (usa asyncio para compatibilidade com FastAPI)
scheduler = AsyncIOScheduler() 

def initialize_firebase_admin():
    """Inicializa o Firebase Admin SDK com as credenciais."""
    try:
        # Caminho absoluto para a chave de serviço
        base_dir = Path(__file__).resolve().parent.parent
        cred_path = base_dir / SERVICE_ACCOUNT_FILE

        if not cred_path.exists():
            print(f"ERRO: Chave do Firebase Admin não encontrada em {cred_path}")
            return None

        cred = credentials.Certificate(str(cred_path))
        # Inicializa o app Firebase (uma vez)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK inicializado com sucesso!")
        return messaging
        
    except Exception as e:
        print(f"Falha ao inicializar o Firebase Admin SDK: {e}")
        return None

# Inicializa o módulo de mensagens
fcm_messaging = initialize_firebase_admin()

# -----------------------------------------------------------
# Lógica de Agendamento e Envio
# -----------------------------------------------------------

async def send_exam_reminder(token: str, exam_name: str, exam_date: str):
    """Função que será executada pelo agendador para enviar a notificação Push."""
    if not fcm_messaging:
        print("FCM não está inicializado. Falha ao enviar lembrete.")
        return

    # O payload da notificação que será exibido na tela do Android
    notification_payload = messaging.Notification(
        title='⏰ Lembrete: Exame Próximo!',
        body=f'O exame "{exam_name}" está agendado para {exam_date}. Prepare-se!',
    )
    
    message = messaging.Message(
        notification=notification_payload,
        token=token,
        # Você pode adicionar dados personalizados aqui, se precisar
        data={
            "screen": "lembretes", 
            "exam_name": exam_name,
        }
    )

    try:
        response = fcm_messaging.send(message)
        print(f"Mensagem FCM enviada com sucesso: {response}")
    except Exception as e:
        print(f"Erro ao enviar mensagem FCM para o token {token}: {e}")

def schedule_reminder(user_id: str, token: str, exam_name: str, exam_date_str: str):
    """Calcula e agenda o lembrete para 3 dias antes do exame."""
    
    try:
        # Tenta parsear a data para 'YYYY-MM-DD'
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d')
    except ValueError as e:
        print(f"Erro de formato de data: {e}")
        return

    # Data para agendar o lembrete (3 dias antes, às 9h00 da manhã)
    reminder_date = exam_date - timedelta(days=3)
    reminder_date = reminder_date.replace(hour=9, minute=0, second=0)
    
    # Se a data de lembrete já passou, agendar para daqui a 1 minuto para fins de teste
    if reminder_date < datetime.now():
         reminder_date = datetime.now() + timedelta(minutes=1) 
         print(f"Aviso: Data de lembrete no passado, agendando para o próximo minuto ({reminder_date.strftime('%Y-%m-%d %H:%M:%S')}).")

    # Cria um ID de trabalho único para o APScheduler
    job_id = f"reminder_{user_id}_{exam_name}_{exam_date_str}" 
    
    # Adiciona a tarefa ao agendador (chama a função assíncrona)
    scheduler.add_job(
        send_exam_reminder, 
        'date', 
        run_date=reminder_date, 
        args=[token, exam_name, exam_date_str],
        id=job_id,
        replace_existing=True
    )
    print(f"Lembrete agendado para {reminder_date.strftime('%Y-%m-%d %H:%M:%S')} com ID: {job_id}")