"""add production authentication sessions and credential storage"""

import sqlalchemy as sa
from alembic import op

revision = "20260815_0005"
down_revision = "20260814_0004"


def upgrade() -> None:
    op.add_column("auth_identities", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE auth_identities SET updated_at = created_at WHERE updated_at IS NULL")
    with op.batch_alter_table("auth_identities") as batch:
        batch.alter_column("updated_at", nullable=False)
    op.create_table(
        "password_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("auth_identity_id", sa.String(36), sa.ForeignKey("auth_identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("password_hash", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("auth_identity_id", name="uq_password_credential_identity"),
    )
    op.create_index("ix_password_credentials_auth_identity_id", "password_credentials", ["auth_identity_id"], unique=True)
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("active_workspace_id", sa.String(36), sa.ForeignKey("organizations.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("token_hash", name="uq_user_session_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])
    with op.batch_alter_table("notifications") as batch:
        batch.create_foreign_key("fk_notifications_user_id_users", "users", ["user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch:
        batch.drop_constraint("fk_notifications_user_id_users", type_="foreignkey")
    op.drop_table("user_sessions")
    op.drop_table("password_credentials")
    with op.batch_alter_table("auth_identities") as batch:
        batch.drop_column("updated_at")
