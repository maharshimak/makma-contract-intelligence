from app.database import SessionLocal
from app.models import Opportunity, PlatformRole, User
from app.seed import seed
from sqlalchemy import func, select


def test_seed_is_idempotent():
    seed()
    seed()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Opportunity)) == 24
        assert db.scalar(
            select(func.count()).select_from(User).where(
                User.is_demo.is_(True),
                User.platform_role.in_([PlatformRole.admin, PlatformRole.superadmin]),
            )
        ) == 0
