from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_service import hash_token
from app.config import get_settings
from app.database import get_db
from app.models import (
    AuditLog,
    MembershipRole,
    Organization,
    OrganizationMember,
    PlatformRole,
    User,
    UserSession,
)


@dataclass(frozen=True)
class Principal:
    user: User
    organization: Organization | None
    membership: OrganizationMember | None
    session: UserSession | None = None


def _unauthenticated() -> HTTPException:
    return HTTPException(
        401,
        detail={"code": "authentication_required", "message": "Sign in to continue"},
        headers={"WWW-Authenticate": "Session"},
    )


def current_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    user: User | None = None
    user_session: UserSession | None = None
    requested_workspace = request.headers.get("X-Workspace-Id")

    if token:
        user_session = db.scalar(
            select(UserSession).where(
                UserSession.token_hash == hash_token(token),
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        if user_session:
            user = db.scalar(
                select(User).where(User.id == user_session.user_id, User.status == "ACTIVE")
            )
            requested_workspace = user_session.active_workspace_id
            user_session.last_seen_at = datetime.now(UTC)
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
                csrf_header = request.headers.get("X-CSRF-Token")
                if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header or hash_token(csrf_header) != user_session.csrf_token_hash:
                    raise HTTPException(403, detail={"code": "csrf_failed", "message": "CSRF validation failed"})
    elif settings.demo_mode and settings.environment != "production":
        demo_email = request.headers.get("X-Demo-User")
        if demo_email:
            user = db.scalar(select(User).where(User.email == demo_email, User.is_demo.is_(True), User.status == "ACTIVE"))
    if user is None:
        raise _unauthenticated()

    memberships = list(
        db.scalars(select(OrganizationMember).where(OrganizationMember.user_id == user.id, OrganizationMember.status == "ACTIVE"))
    )
    membership = None
    if requested_workspace:
        membership = next((item for item in memberships if item.organization_id == requested_workspace), None)
        if membership is None:
            raise HTTPException(403, detail={"code": "workspace_forbidden", "message": "User is not an active member of this workspace"})
    elif memberships:
        membership = memberships[0]
        if user_session:
            user_session.active_workspace_id = membership.organization_id
            db.commit()
    organization = db.get(Organization, membership.organization_id) if membership else None
    return Principal(user=user, organization=organization, membership=membership, session=user_session)


MANAGER_ROLES = {MembershipRole.owner, MembershipRole.admin, MembershipRole.sales_director, MembershipRole.bid_manager}


def require_manager(principal: Principal = Depends(current_principal)) -> Principal:
    if principal.membership is None or principal.membership.role not in MANAGER_ROLES:
        raise HTTPException(403, detail={"code": "manager_role_required", "message": "An active manager membership is required"})
    return principal


def require_platform_admin(
    principal: Principal = Depends(current_principal), db: Session = Depends(get_db)
) -> Principal:
    if principal.user.platform_role not in {PlatformRole.admin, PlatformRole.superadmin}:
        db.add(AuditLog(actor_user_id=principal.user.id, organization_id=principal.organization.id if principal.organization else None, action="security.admin_access_blocked", entity_type="user", entity_id=principal.user.id))
        db.commit()
        raise HTTPException(403, detail={"code": "admin_required", "message": "Platform administrator access is required"})
    return principal
