"""Server management routes: register a server to monitor (demo or real EC2)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from database import models
from database.schemas import ServerCreate, ServerOut
from services.auth_service import get_current_user
from demo import simulated_server

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.post("", response_model=ServerOut, status_code=201)
def create_server(payload: ServerCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    server = models.Server(**payload.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    if server.is_demo:
        simulated_server.reset_state()
    return server


@router.get("", response_model=List[ServerOut])
def list_servers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Server).all()


@router.get("/{server_id}", response_model=ServerOut)
def get_server(server_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    server = db.query(models.Server).get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server
