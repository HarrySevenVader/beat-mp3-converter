from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.convert import router as convert_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
)

app.include_router(convert_router)

@app.get("/")
def read_root():
    return {"Servidor funcionando🚀"}