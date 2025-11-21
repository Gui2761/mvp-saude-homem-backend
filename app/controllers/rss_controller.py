from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.rss_service import buscar_rss

router = APIRouter(prefix="/rss", tags=["RSS"])

@router.get("/", response_class=JSONResponse)
def get_rss(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(3, ge=1, description="Itens por página")
):
    # 1. Busca todas as notícias
    todas_noticias = buscar_rss()
    
    # 2. Calcula o total
    total_noticias = len(todas_noticias)
    
    # 3. Faz a paginação (fatia a lista)
    inicio = (page - 1) * limit
    fim = inicio + limit
    noticias_paginadas = todas_noticias[inicio:fim]
    
    # 4. Retorna no formato que o Flutter espera (Map/Dicionário)
    return JSONResponse(content={
        "noticias": noticias_paginadas,
        "totalNoticias": total_noticias,
        "paginaAtual": page,
        "noticiasPorPagina": limit
    })