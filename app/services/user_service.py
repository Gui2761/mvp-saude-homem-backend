# gui2761/mvp-saude-homem-backend/app/services/user_service.py

from borneo import PutRequest, GetRequest, QueryRequest, TableRequest, TableLimits
from app.database import db
from app.utils.auth import AuthUtils
from app.schemas.user_schema import UserCreate, UserLogin, PasswordReset
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class UserService:
    def __init__(self):
        # 🟢 MUDANÇA 1: Nome da tabela alterado para evitar conflito com a antiga e sem traços
        self.table_name = "UsersV2"
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        """Cria tabela Users se não existir"""
        try:
            create_table_ddl = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                user_id STRING,
                name STRING,
                email STRING,
                password_hash STRING,
                security_word STRING,
                device_tokens ARRAY(RECORD(token STRING, platform STRING, last_used TIMESTAMP(3))), 
                created_at TIMESTAMP(3),
                updated_at TIMESTAMP(3),
                is_active BOOLEAN,
                PRIMARY KEY(user_id)
            )
            """
            request = TableRequest().set_statement(create_table_ddl)
            
            # 🟢 MUDANÇA 2: Definindo limites de Throughput e Capacidade (Obrigatório na Nuvem)
            # Leitura: 50 unidades, Escrita: 50 unidades, Armazenamento: 25 GB (Limites do Free Tier geralmente)
            limits = TableLimits(50, 50, 25)
            request.set_table_limits(limits)

            db.handle.table_request(request)
            print(f"Tabela {self.table_name} criada/verificada com sucesso!")
        except Exception as e:
            print(f"Tabela {self.table_name} já existe ou erro: {e}")

    async def save_device_token(self, user_id: str, device_token: str, platform: Optional[str] = "android"):
        """Salva ou atualiza o token do dispositivo para o usuário."""
        user = await self.get_user_by_id(user_id, include_sensitive=True) 
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

        # Garante que 'device_tokens' é uma lista
        user.setdefault('device_tokens', []) 
        
        tokens: List[Dict[str, str]] = user['device_tokens']
        
        # Remove token se já existir para evitar duplicatas
        tokens = [t for t in tokens if t.get('token') != device_token]
        
        tokens.append({
            "token": device_token,
            "platform": platform,
            "last_used": datetime.utcnow().isoformat()
        })
        
        user['device_tokens'] = tokens
        user["updated_at"] = datetime.utcnow().isoformat()

        put_request = PutRequest().set_table_name(self.table_name).set_value(user)
        db.handle.put(put_request)


    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Registra novo usuário"""
        if await self._email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )

        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        user_doc = {
            "user_id": user_id,
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": AuthUtils.hash_password(user_data.password),
            "security_word": user_data.security_word.lower(),
            "device_tokens": [],
            "is_active": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        put_request = PutRequest().set_table_name(self.table_name).set_value(user_doc)
        db.handle.put(put_request)

        access_token = AuthUtils.create_access_token({"sub": user_id})
        refresh_token = AuthUtils.create_refresh_token({"sub": user_id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user_id,
                "name": user_data.name,
                "email": user_data.email,
                "created_at": now
            }
        }

    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Faz login do usuário"""

        user = await self._get_user_by_email(login_data.identifier)
        
        if not user:
            user = await self._get_user_by_name(login_data.identifier)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identificador ou senha incorretos"
            )
        
        if not AuthUtils.verify_password(login_data.password, user.get("password_hash", "")):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Identificador ou senha incorretos"
            )

        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Conta desativada"
            )

        access_token = AuthUtils.create_access_token({"sub": user["user_id"]})
        refresh_token = AuthUtils.create_refresh_token({"sub": user["user_id"]})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
        }

    async def reset_password(self, reset_data: PasswordReset) -> Dict[str, str]:
        """Recupera senha usando palavra de segurança"""
        user = await self._get_user_by_email(reset_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email não encontrado")
        if not user.get("is_active", True):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conta desativada")
        if user.get("security_word") != reset_data.security_word.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Palavra de segurança incorreta")

        user["password_hash"] = AuthUtils.hash_password(reset_data.new_password)
        user["updated_at"] = datetime.utcnow().isoformat()
        put_request = PutRequest().set_table_name(self.table_name).set_value(user)
        db.handle.put(put_request)
        return {"message": "Senha alterada com sucesso"}

    async def _email_exists(self, email: str) -> bool:
        """Verifica se email já existe"""
        user = await self._get_user_by_email(email)
        return user is not None

    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        if "@" not in email:
            return None 

        query = f"SELECT * FROM {self.table_name} WHERE email = '{email}'"
        request = QueryRequest().set_statement(query)
        result = db.handle.query(request)
        return result.get_results()[0] if result.get_results() else None

    async def _get_user_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo nome"""
        query = f"SELECT * FROM {self.table_name} WHERE name = '{name}'"
        request = QueryRequest().set_statement(query)
        result = db.handle.query(request)
        return result.get_results()[0] if result.get_results() else None

    async def get_user_by_id(self, user_id: str, include_sensitive: bool = False) -> Optional[Dict[str, Any]]:
        """Busca usuário por ID"""
        get_request = GetRequest().set_table_name(self.table_name).set_key({"user_id": user_id})
        result = db.handle.get(get_request)
        if result.get_value():
            user = result.get_value()
            
            if include_sensitive:
                 user.setdefault('device_tokens', []) 
                 
            if not include_sensitive:
                user.pop("password_hash", None)
                user.pop("security_word", None)
                user.pop("device_tokens", None)
            return user
        return None


# Instância do serviço
user_service = UserService()