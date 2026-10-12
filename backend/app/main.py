"""Ponto de entrada.

    cd backend
    uvicorn app.main:app --reload

Docs em http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router

app = FastAPI(
    title="Basqueteleiro API",
    version="0.1.0",
    description="Notícias de basquete (NBB, futuramente LDB, Liga Ouro e NBA).",
)

# CORS: permite que o frontend (rodando em outra porta ou como file://)
# consiga chamar esta API. Em dev libera tudo; em produção, restrinja.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # em prod: ["https://basqueteleiro.com.br"]
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Home"])
def raiz() -> dict[str, str]:
    return {"mensagem": "Basqueteleiro API viva. Veja /docs para explorar."}