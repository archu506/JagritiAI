from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, query, consent, awareness, content, dashboard, compat, asha

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(query.router, prefix=settings.API_V1_PREFIX)
app.include_router(consent.router, prefix=settings.API_V1_PREFIX)
app.include_router(awareness.router, prefix=settings.API_V1_PREFIX)
app.include_router(content.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(compat.router, prefix=settings.API_V1_PREFIX)
app.include_router(asha.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
