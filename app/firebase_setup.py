import firebase_admin
from firebase_admin import credentials, messaging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os

CREDENTIALS_PATH = "firebase-service-account.json"

def initialize_firebase():
    if not firebase_admin._apps:
        if os.path.exists(CREDENTIALS_PATH):
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado com sucesso!")
        else:
            print(f"ERRO: Arquivo de credenciais não encontrado em {CREDENTIALS_PATH}")

def send_fcm_message(token: str, title: str, body: str):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        response = messaging.send(message)
        print('Mensagem FCM enviada com sucesso:', response)
    except Exception as e:
        print('Erro ao enviar mensagem FCM:', e)

scheduler = BackgroundScheduler()
scheduler.start()

# 🟢 ATUALIZADO: Removido parâmetro recurrence e lógica complexa
def schedule_reminder(user_id: str, token: str, exam_name: str, exam_date_str: str):
    """
    Agenda um lembrete único para 3 dias antes do exame.
    """
    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
        
        # Data do aviso (3 dias antes)
        run_date = exam_date - timedelta(days=3)
        
        # Se já passou (para testes), joga para 1 minuto no futuro
        if run_date < datetime.now():
            run_date = datetime.now() + timedelta(minutes=1)

        job_id = f"reminder_{user_id}_{exam_name}_{exam_date_str}"

        # 🟢 Usa trigger='date' para executar UMA vez na data específica
        scheduler.add_job(
            send_fcm_message,
            trigger='date',
            run_date=run_date,
            id=job_id,
            args=[token, "Lembrete de Exame", f"Não esqueça do seu exame: {exam_name}! É daqui a 3 dias."],
            replace_existing=True
        )
        print(f"Lembrete agendado para {run_date}")

    except Exception as e:
        print(f"Erro ao agendar lembrete: {e}")