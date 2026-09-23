from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import SESSION_COOKIE, require_admin
from app.api.rate_limit import SlidingWindowLimiter
from app.config import settings
from app.db import get_db
from app.models import AdminUser
from app.schemas import LoginIn, MeOut
from app.security import sign_session
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])
_limiter = SlidingWindowLimiter(settings.login_rate_limit, 300)


@router.post("/login", status_code=204)
def login(
    body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)
) -> None:
    ip = request.client.host if request.client else "unknown"
    if not _limiter.hit(ip):
        raise HTTPException(status_code=429, detail="Too many attempts")
    user = authenticate(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    response.set_cookie(
        SESSION_COOKIE,
        sign_session(user.id),
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.env == "production",
        path="/",
    )


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=MeOut)
def me(user: AdminUser = Depends(require_admin)) -> MeOut:
    return MeOut(email=user.email)
