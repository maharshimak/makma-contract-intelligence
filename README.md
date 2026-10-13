# Contract Intelligence OS

Status: **NEEDS WORK**. This is a clean local publication-preparation copy, not a tested release or an approved GitHub upload.

Next.js company/opportunity/pipeline UI -> FastAPI identity/session/CSRF/RBAC -> domain scoring/qualification/network/procurement adapters -> SQLAlchemy/Alembic database.

Implemented source scope: Company onboarding, opportunity discovery and qualification, matching/scoring, pipeline updates, buyer intelligence, team access, saved searches/notifications, password identities and hashed session tokens.

The original source was not modified. Secrets, existing databases, media, model weights, binary tools, personal outputs and dependency/generated directories are absent. Credentials are blank in `.env.example`; obtain operator values privately only after the next execution step is approved. Code source rights/licensing remain to be confirmed; no license was fabricated.

See [SETUP.md](SETUP.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY_REVIEW.md](SECURITY_REVIEW.md), [TECHNICAL_ISSUES.md](TECHNICAL_ISSUES.md), [DEPENDENCY_REVIEW.md](DEPENDENCY_REVIEW.md), [READINESS.md](READINESS.md) and [CHANGES.md](CHANGES.md). SOURCE_MANIFEST.csv lists the exact inspected source paths/hashes and EXCLUDED_FILES.csv records exclusions. Static syntax/config checks do not establish passing tests/builds.

Entry point: `apps/api/app/main.py`. Frontend source: `apps/web`. Proposed name: `contract-intelligence-os`. Proposed visibility: **private for initial review; public only after security, ownership/license and verification clearance**.
