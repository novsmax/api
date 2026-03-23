from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, roles, goals, password

app = FastAPI(
    title="Smart Tracker API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(goals.router)
app.include_router(password.router)

@app.get("/")
async def root():
    return {"message": "Smart Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}