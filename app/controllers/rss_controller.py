from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.rss_service import buscar_rss

router = APIRouter(prefix="/rss", tags=["RSS"])


@router.get("/", response_class=JSONResponse)
def get_rss():
    dados = buscar_rss()
    return JSONResponse(content=dados)