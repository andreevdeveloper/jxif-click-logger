import secrets
import string
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyHttpUrl
from sqlmodel import Session, select

from common.db import create_db_and_tables, get_session
from common.models import Link, Click
from common.settings import settings


ALPHABET = string.ascii_letters + string.digits


def gen_code(n: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


class LinkCreate(BaseModel):
    target_url: AnyHttpUrl
    code: Optional[str] = None


class LinkRead(BaseModel):
    id: int
    code: str
    target_url: str
    created_at: datetime
    tracking_url: str
    tracking_url_js: str


class ClickRead(BaseModel):
    id: int
    code: str
    target_url: str
    created_at: datetime
    ip: Optional[str]
    forwarded_for: Optional[str]
    user_agent: Optional[str]
    accept_language: Optional[str]
    referer: Optional[str]
    method: str
    path: str
    query: dict
    client: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="admin-service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "service": "admin"}


@app.post("/links", response_model=LinkRead)
def create_link(payload: LinkCreate, session: Session = Depends(get_session)):
    code = payload.code or gen_code()

    exists = session.exec(select(Link).where(Link.code == code)).first()
    if exists:
        raise HTTPException(status_code=409, detail="Code already exists")

    link = Link(code=code, target_url=str(payload.target_url))
    session.add(link)
    session.commit()
    session.refresh(link)

    base = settings.public_tracker_url.rstrip("/")
    tracking_url = f"{base}/t/{link.code}"
    return LinkRead(
        id=link.id,
        code=link.code,
        target_url=link.target_url,
        created_at=link.created_at,
        tracking_url=tracking_url,
        tracking_url_js=tracking_url + "?js=1",
    )


@app.get("/links", response_model=list[LinkRead])
def list_links(session: Session = Depends(get_session)):
    base = settings.public_tracker_url.rstrip("/")
    links = session.exec(select(Link).order_by(Link.created_at.desc())).all()
    out: list[LinkRead] = []
    for link in links:
        tracking_url = f"{base}/t/{link.code}"
        out.append(
            LinkRead(
                id=link.id,
                code=link.code,
                target_url=link.target_url,
                created_at=link.created_at,
                tracking_url=tracking_url,
                tracking_url_js=tracking_url + "?js=1",
            )
        )
    return out


@app.get("/clicks", response_model=list[ClickRead])
def list_clicks(
    code: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = (
        select(Click, Link)
        .join(Link, Click.link_id == Link.id)
        .order_by(Click.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if code:
        stmt = stmt.where(Link.code == code)

    rows = session.exec(stmt).all()

    result: list[ClickRead] = []
    for click, link in rows:
        result.append(
            ClickRead(
                id=click.id,
                code=link.code,
                target_url=link.target_url,
                created_at=click.created_at,
                ip=click.ip,
                forwarded_for=click.forwarded_for,
                user_agent=click.user_agent,
                accept_language=click.accept_language,
                referer=click.referer,
                method=click.method,
                path=click.path,
                query=click.query or {},
                client=click.client or {},
            )
        )
    return result