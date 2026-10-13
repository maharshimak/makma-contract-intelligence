import argparse

from sqlalchemy import select

from app.auth_service import normalize_email
from app.database import SessionLocal
from app.models import AuditLog, PlatformRole, User, utcnow


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote an existing verified user to platform admin")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=["ADMIN", "SUPERADMIN"], default="ADMIN")
    parser.add_argument("--reason", required=True)
    parser.add_argument(
        "--confirm-email-verified",
        action="store_true",
        help="Record that the operator independently verified this email",
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == normalize_email(args.email)))
        if user is None:
            raise SystemExit("Refusing bootstrap: user does not exist")
        if user.email_verified_at is None and not args.confirm_email_verified:
            raise SystemExit("Refusing bootstrap: email is not verified")
        if user.is_demo:
            raise SystemExit("Refusing bootstrap: demo identities cannot be promoted")
        if user.email_verified_at is None:
            user.email_verified_at = utcnow()
        user.platform_role = PlatformRole(args.role)
        db.add(AuditLog(actor_user_id=user.id, action="platform_role.bootstrap", entity_type="user", entity_id=user.id, reason=args.reason, audit_metadata={"role": args.role, "operator_confirmed_email": args.confirm_email_verified}))
        db.commit()
        print(f"Promoted {user.email} to {args.role}; audit event recorded")


if __name__ == "__main__":
    main()
