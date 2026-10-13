import re
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import Principal, current_principal
from app.auth_service import (
    auth_rate_limiter,
    create_password_identity,
    create_session,
    normalize_email,
    verify_password_identity,
)
from app.config import get_settings
from app.database import get_db
from app.models import (
    AuditLog,
    CompanyProfile,
    MembershipRole,
    Organization,
    OrganizationMember,
    ProfessionalProfile,
    User,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)


class SignupWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_type: Literal["COMPANY", "PROFESSIONAL"]
    email: str = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=200)
    company_name: str | None = Field(default=None, min_length=2, max_length=200)


class DemoLoginWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persona: Literal["company", "professional"]


def _slug(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "company"
    return base


def _set_session_cookies(response: Response, token: str, csrf_token: str) -> None:
    settings = get_settings()
    max_age = settings.session_lifetime_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _rate_limit(request: Request, email: str = "") -> None:
    settings = get_settings()
    client = request.client.host if request.client else "unknown"
    if not auth_rate_limiter.check(f"{request.url.path}:{client}:{email.casefold()}", settings):
        raise HTTPException(429, detail={"code": "rate_limited", "message": "Try again later"})


def _require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("Origin")
    if origin and origin not in get_settings().cors_origin_list:
        raise HTTPException(403, detail={"code": "origin_forbidden", "message": "Request origin is not trusted"})


@router.post("/login", status_code=204)
def login(
    payload: LoginWrite, request: Request, response: Response, db: Session = Depends(get_db)
) -> None:
    _require_trusted_origin(request)
    _rate_limit(request, payload.email)
    user = verify_password_identity(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            401, detail={"code": "invalid_credentials", "message": "Invalid email or password"}
        )
    user.last_login_at = datetime.now(UTC)
    session = create_session(db, user, get_settings())
    db.add(AuditLog(actor_user_id=user.id, action="auth.login", entity_type="user", entity_id=user.id))
    db.commit()
    _set_session_cookies(response, session.token, session.csrf_token)


@router.post("/signup", status_code=201)
def signup(
    payload: SignupWrite, request: Request, response: Response, db: Session = Depends(get_db)
) -> dict[str, str]:
    _require_trusted_origin(request)
    _rate_limit(request, payload.email)
    try:
        email = normalize_email(payload.email)
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(409, detail={"code": "email_in_use", "message": "Email is already registered"})
        if payload.account_type == "COMPANY" and not payload.company_name:
            raise HTTPException(422, detail={"code": "company_name_required", "message": "Company name is required"})
        user = User(email=email, display_name=payload.display_name.strip(), email_verified_at=None)
        db.add(user)
        db.flush()
        create_password_identity(db, user, payload.password)
        if payload.account_type == "COMPANY":
            assert payload.company_name is not None
            slug = _slug(payload.company_name)
            if db.scalar(select(Organization.id).where(Organization.slug == slug)):
                slug = f"{slug}-{user.id[:8]}"
            organization = Organization(name=payload.company_name.strip(), slug=slug)
            db.add(organization)
            db.flush()
            db.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role=MembershipRole.owner))
            db.add(CompanyProfile(organization_id=organization.id, company_name=payload.company_name.strip()))
        else:
            db.add(ProfessionalProfile(user_id=user.id))
        session = create_session(db, user, get_settings())
        db.add(AuditLog(actor_user_id=user.id, action="auth.signup", entity_type="user", entity_id=user.id, audit_metadata={"account_type": payload.account_type}))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, detail={"code": str(exc), "message": "Email or password does not meet requirements"}) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, detail={"code": "signup_conflict", "message": "Account could not be created"}) from exc
    _set_session_cookies(response, session.token, session.csrf_token)
    return {"account_type": payload.account_type}


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> None:
    if principal.session:
        principal.session.revoked_at = datetime.now(UTC)
    db.add(AuditLog(actor_user_id=principal.user.id, action="auth.logout", entity_type="user", entity_id=principal.user.id))
    db.commit()
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


@router.post("/demo-login", status_code=204)
def demo_login(payload: DemoLoginWrite, request: Request, response: Response, db: Session = Depends(get_db)) -> None:
    _require_trusted_origin(request)
    settings = get_settings()
    if not settings.demo_mode or settings.environment == "production":
        raise HTTPException(404, detail={"code": "not_found", "message": "Not found"})
    _rate_limit(request, payload.persona)
    emails = {"company": "user-d9853303@example.test", "professional": "user-2e6ef0f9@example.test"}
    user = db.scalar(select(User).where(User.email == emails[payload.persona], User.is_demo.is_(True)))
    if user is None:
        raise HTTPException(503, detail={"code": "demo_not_seeded", "message": "Demo data is not installed"})
    session = create_session(db, user, settings)
    db.commit()
    _set_session_cookies(response, session.token, session.csrf_token)
