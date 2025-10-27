from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.rss_service import buscar_todas_rss # Importar a nova função

router = APIRouter(prefix="/rss", tags=["RSS"])

@router.get("/", response_class=JSONResponse)
def get_rss_feed(
    page: int = Query(1, ge=1, description="Número da página (começando em 1)"),
    limit: int = Query(3, ge=1, le=100, description="Número de notícias por página")
):
    """
    Endpoint que retorna notícias de saúde do feed RSS com paginação.
    """
    todas_noticias = buscar_todas_rss()
    
    # Tratamento de erro se buscar_todas_rss retornar um erro
    if todas_noticias and "error" in todas_noticias[0]:
        return JSONResponse(content=todas_noticias, status_code=500) # Retorna o erro com status 500

    total_noticias = len(todas_noticias)
    
    start = (page - 1) * limit
    end = start + limit
    
    noticias_paginadas = todas_noticias[start:end]
    
    # Retorna as notícias paginadas junto com o total e informações da paginação
    return JSONResponse(content={
        "noticias": noticias_paginadas,
        "totalNoticias": total_noticias,
        "paginaAtual": page,
        "noticiasPorPagina": limit
    })