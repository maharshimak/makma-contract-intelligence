import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    AuthIdentity,
    Buyer,
    CapabilityGap,
    CompanyProfile,
    GapType,
    Invitation,
    MembershipRole,
    Notification,
    Opportunity,
    Organization,
    OrganizationMember,
    PipelineItem,
    PipelineStage,
    PlatformRole,
    ProfessionalProfile,
    User,
    WorkPost,
    WorkPostType,
    utcnow,
)
from app.services import opportunity_value, recalculate_matches

logger = logging.getLogger("contract_os.seed")

BUYERS = [
    ("hospital-paris", "Groupe Hospitalier Métropolitain", "hospital", "Paris", "Île-de-France"),
    (
        "region-idf",
        "Agence Numérique Francilienne",
        "regional agency",
        "Saint-Denis",
        "Île-de-France",
    ),
    ("univ-lyon", "Université Nouvelle de Lyon", "university", "Lyon", "Auvergne-Rhône-Alpes"),
    ("city-nantes", "Ville de Nantes Métropole Démo", "city", "Nantes", "Pays de la Loire"),
    ("ministry-demo", "Direction Interministérielle Démo", "ministry", "Paris", "Île-de-France"),
    ("hospital-lille", "Centre Hospitalier des Flandres", "hospital", "Lille", "Hauts-de-France"),
    (
        "region-paca",
        "Agence Territoriale Méditerranée",
        "regional agency",
        "Marseille",
        "Provence-Alpes-Côte d'Azur",
    ),
    ("city-bordeaux", "Bordeaux Services Publics Démo", "city", "Bordeaux", "Nouvelle-Aquitaine"),
]

OPPORTUNITIES = [
    (
        "AI-assisted document classification platform",
        650000,
        900000,
        "Île-de-France",
        ["Artificial Intelligence", "Data Science"],
        ["Python", "NLP", "Machine Learning"],
        ["ISO 27001"],
        18,
        0,
    ),
    (
        "Generative AI knowledge assistant",
        420000,
        680000,
        "Île-de-France",
        ["Generative AI", "Software Development"],
        ["RAG", "LLM", "Python"],
        [],
        12,
        1,
    ),
    (
        "Hospital data platform modernization",
        1000000,
        1400000,
        "Île-de-France",
        ["Data Engineering", "Cloud Engineering"],
        ["PostgreSQL", "Azure", "Docker"],
        ["HDS"],
        25,
        0,
    ),
    (
        "Machine learning demand forecasting system",
        280000,
        450000,
        "Auvergne-Rhône-Alpes",
        ["Machine Learning", "Data Science"],
        ["Python", "Machine Learning"],
        [],
        9,
        2,
    ),
    (
        "Data warehouse modernization",
        1100000,
        1500000,
        "Île-de-France",
        ["Data Engineering", "Business Intelligence"],
        ["PostgreSQL", "AWS"],
        [],
        32,
        4,
    ),
    (
        "Cloud migration support",
        500000,
        850000,
        "Pays de la Loire",
        ["Cloud Engineering"],
        ["AWS", "Azure", "Kubernetes"],
        ["ISO 27001"],
        21,
        3,
    ),
    (
        "Natural language citizen-services assistant",
        180000,
        320000,
        "Île-de-France",
        ["Natural Language Processing", "Generative AI"],
        ["NLP", "RAG"],
        [],
        6,
        1,
    ),
    (
        "Public-sector API platform",
        750000,
        1100000,
        "Île-de-France",
        ["Software Development", "Cloud Engineering"],
        ["FastAPI", "Python", "Docker"],
        [],
        27,
        4,
    ),
    (
        "Business intelligence reporting platform",
        240000,
        390000,
        "Hauts-de-France",
        ["Business Intelligence", "Data Engineering"],
        ["PostgreSQL", "Python"],
        [],
        14,
        5,
    ),
    (
        "Research data lake architecture",
        1300000,
        1900000,
        "Auvergne-Rhône-Alpes",
        ["Data Engineering", "Cloud Engineering"],
        ["AWS", "Kubernetes"],
        [],
        39,
        2,
    ),
    (
        "Digital transformation consulting",
        350000,
        600000,
        "Nouvelle-Aquitaine",
        ["Consulting"],
        [],
        [],
        16,
        7,
    ),
    (
        "Cybersecurity monitoring center",
        1000000,
        1800000,
        "Provence-Alpes-Côte d'Azur",
        ["Cybersecurity"],
        [],
        ["ISO 27001", "PASSI"],
        28,
        6,
    ),
    (
        "Municipal website redesign",
        90000,
        140000,
        "Pays de la Loire",
        ["Web Design"],
        ["JavaScript"],
        [],
        10,
        3,
    ),
    (
        "Road infrastructure maintenance",
        2800000,
        5000000,
        "Nouvelle-Aquitaine",
        ["Road Maintenance"],
        [],
        [],
        41,
        7,
    ),
    (
        "Public building cleaning services",
        600000,
        950000,
        "Hauts-de-France",
        ["Cleaning Services"],
        [],
        ["ISO 14001"],
        8,
        5,
    ),
    (
        "Small data quality assessment",
        50000,
        75000,
        "Île-de-France",
        ["Data Science"],
        ["Python"],
        [],
        5,
        4,
    ),
    (
        "European sovereign cloud framework",
        3200000,
        5000000,
        "Bruxelles",
        ["Cloud Engineering"],
        ["Kubernetes", "Azure"],
        ["ISO 27001"],
        48,
        4,
    ),
    (
        "Predictive maintenance analytics",
        340000,
        520000,
        "Provence-Alpes-Côte d'Azur",
        ["Machine Learning", "Data Engineering"],
        ["Python", "Machine Learning"],
        [],
        19,
        6,
    ),
    (
        "University RAG research portal",
        160000,
        260000,
        "Auvergne-Rhône-Alpes",
        ["Generative AI", "Software Development"],
        ["RAG", "NLP", "Python"],
        [],
        23,
        2,
    ),
    (
        "Kubernetes application platform support",
        700000,
        1200000,
        "Île-de-France",
        ["Cloud Engineering", "Software Development"],
        ["Kubernetes", "Docker", "AWS"],
        [],
        30,
        1,
    ),
    (
        "Financial records OCR and classification",
        220000,
        370000,
        "Île-de-France",
        ["Artificial Intelligence", "Data Science"],
        ["NLP", "Python"],
        [],
        11,
        4,
    ),
    (
        "Legacy ERP replacement program",
        1800000,
        2600000,
        "Pays de la Loire",
        ["ERP"],
        ["SAP"],
        [],
        37,
        3,
    ),
    (
        "Open data publication pipeline",
        190000,
        330000,
        "Nouvelle-Aquitaine",
        ["Data Engineering", "Software Development"],
        ["Python", "PostgreSQL"],
        [],
        15,
        7,
    ),
    (
        "Clinical NLP experimentation environment",
        480000,
        720000,
        "Hauts-de-France",
        ["Natural Language Processing", "Data Science"],
        ["NLP", "Python", "Docker"],
        ["HDS"],
        26,
        5,
    ),
]


def seed() -> None:
    with SessionLocal() as db:
        org = db.scalar(select(Organization).where(Organization.slug == "datanova-sas"))
        if not org:
            org = Organization(
                name="DataNova SAS",
                slug="datanova-sas",
                organization_type="SUPPLIER",
                verification_status="DEMO_VERIFIED",
                is_demo=True,
            )
            db.add(org)
            db.flush()
        company = db.scalar(select(CompanyProfile).where(CompanyProfile.organization_id == org.id))
        if not company:
            company = CompanyProfile(
                organization_id=org.id,
                company_name="DataNova SAS",
                siren="123456789",
                website="https://datanova.example",
                description="Synthetic demo profile for an AI and data engineering consultancy.",
                employee_count=24,
                annual_revenue=Decimal("4200000"),
                headquarters_city="Paris",
                headquarters_region="Île-de-France",
                headquarters_country="FR",
                operating_regions=["Île-de-France", "France"],
                service_categories=[
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Data Science",
                    "Data Engineering",
                    "Natural Language Processing",
                    "Generative AI",
                    "RAG",
                    "Cloud Engineering",
                    "Software Development",
                ],
                technologies=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "AWS",
                    "Azure",
                    "Docker",
                    "Kubernetes",
                    "Machine Learning",
                    "LLM",
                    "RAG",
                    "NLP",
                ],
                certifications=["AWS"],
                preferred_contract_min=Decimal("100000"),
                preferred_contract_max=Decimal("1500000"),
                preferred_geographies=["Île-de-France", "France"],
                preferred_buyer_types=["hospital", "regional agency", "ministry", "university"],
                preferred_categories=[
                    "Artificial Intelligence",
                    "Data Engineering",
                    "Machine Learning",
                    "Generative AI",
                    "Cloud Engineering",
                ],
                excluded_categories=["Cleaning Services", "Road Maintenance"],
            )
            db.add(company)
            db.flush()
        owner = db.scalar(select(User).where(User.email == "user-d9853303@example.test"))
        if owner is None:
            owner = User(
                email="user-d9853303@example.test",
                email_verified_at=utcnow(),
                display_name="Maharshi Patel",
                platform_role=PlatformRole.user,
                is_demo=True,
            )
            db.add(owner)
            db.flush()
            db.add(AuthIdentity(user_id=owner.id, provider="demo", provider_subject=owner.email))
        if not db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id, OrganizationMember.user_id == owner.id
            )
        ):
            db.add(
                OrganizationMember(
                    organization_id=org.id, user_id=owner.id, role=MembershipRole.owner
                )
            )
        analyst = db.scalar(select(User).where(User.email == "user-5179d8ae@example.test"))
        if analyst is None:
            analyst = User(
                email="user-5179d8ae@example.test", display_name="Camille Bernard", is_demo=True
            )
            db.add(analyst)
            db.flush()
            db.add(
                AuthIdentity(user_id=analyst.id, provider="demo", provider_subject=analyst.email)
            )
        if not db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == analyst.id,
            )
        ):
            db.add(
                OrganizationMember(
                    organization_id=org.id, user_id=analyst.id, role=MembershipRole.viewer
                )
            )
        elena_user = db.scalar(select(User).where(User.email == "user-2e6ef0f9@example.test"))
        if elena_user is None:
            elena_user = User(
                email="user-2e6ef0f9@example.test",
                email_verified_at=utcnow(),
                display_name="Elena Martin",
                is_demo=True,
            )
            db.add(elena_user)
            db.flush()
            db.add(
                AuthIdentity(
                    user_id=elena_user.id, provider="demo", provider_subject=elena_user.email
                )
            )
        elena = db.scalar(
            select(ProfessionalProfile).where(ProfessionalProfile.user_id == elena_user.id)
        )
        if elena is None:
            elena = ProfessionalProfile(
                user_id=elena_user.id,
                headline="Senior Cybersecurity Architect",
                bio="Synthetic expert profile for the tender-to-team demonstration.",
                location="Paris",
                country="FR",
                preferred_regions=["France"],
                languages=[
                    {"language": "French", "proficiency": "Native"},
                    {"language": "English", "proficiency": "Fluent"},
                ],
                skills=[
                    "Cybersecurity",
                    "Cloud security",
                    "Risk assessment",
                    "French procurement expertise",
                ],
                technologies=["Azure"],
                certifications=["ISO 27001"],
                industries=["Public sector IT", "Healthcare"],
                procurement_experience=["French procurement expertise"],
                years_experience=14,
                availability_status="AVAILABLE",
                daily_rate=Decimal("950"),
                preferred_engagements=["BID_PROJECT", "EXPERT_REQUEST"],
                remote_preference="HYBRID",
                visibility="NETWORK",
                is_demo=True,
            )
            db.add(elena)
            db.flush()
        admin = db.scalar(select(User).where(User.email == "user-e3945303@example.test"))
        if admin is None:
            admin = User(
                email="user-e3945303@example.test",
                display_name="Network Admin",
                platform_role=PlatformRole.user,
                is_demo=True,
            )
            db.add(admin)
            db.flush()
            db.add(AuthIdentity(user_id=admin.id, provider="demo", provider_subject=admin.email))
        else:
            admin.platform_role = PlatformRole.user
        partner_org = db.scalar(select(Organization).where(Organization.slug == "cybersec-sas"))
        if partner_org is None:
            partner_org = Organization(
                name="CyberSec SAS",
                slug="cybersec-sas",
                organization_type="PARTNER",
                description="Synthetic security delivery partner.",
                country="FR",
                region="Île-de-France",
                city="Paris",
                verification_status="DEMO_VERIFIED",
                is_demo=True,
            )
            db.add(partner_org)
            db.flush()
            db.add(
                CompanyProfile(
                    organization_id=partner_org.id,
                    company_name="CyberSec SAS",
                    description="Synthetic partner specializing in security assurance.",
                    headquarters_city="Paris",
                    headquarters_region="Île-de-France",
                    headquarters_country="FR",
                    operating_regions=["France"],
                    service_categories=["Cybersecurity", "SOC Operations", "Pen testing"],
                    technologies=["Cloud security", "Azure"],
                    certifications=["ISO 27001"],
                    preferred_geographies=["France"],
                    preferred_buyer_types=["hospital", "ministry"],
                    preferred_categories=["Cybersecurity"],
                    excluded_categories=[],
                )
            )
        consulting_org = db.scalar(
            select(Organization).where(Organization.slug == "mp-ai-consulting")
        )
        if consulting_org is None:
            consulting_org = Organization(
                name="MP AI Consulting",
                slug="mp-ai-consulting",
                organization_type="SUPPLIER",
                country="FR",
                verification_status="UNVERIFIED",
                is_demo=True,
            )
            db.add(consulting_org)
            db.flush()
        if not db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == consulting_org.id,
                OrganizationMember.user_id == owner.id,
            )
        ):
            db.add(
                OrganizationMember(
                    organization_id=consulting_org.id, user_id=owner.id, role=MembershipRole.owner
                )
            )
        buyer_records: list[Buyer] = []
        for ext, name, kind, city, region in BUYERS:
            record = db.scalar(
                select(Buyer).where(Buyer.source == "DEMO", Buyer.external_id == ext)
            )
            if not record:
                record = Buyer(
                    source="DEMO",
                    external_id=ext,
                    name=name,
                    buyer_type=kind,
                    city=city,
                    region=region,
                    country="FR",
                    raw_metadata={"fixture": True},
                )
                db.add(record)
                db.flush()
            buyer_records.append(record)
        today = date.today()
        for index, (
            title,
            minimum,
            maximum,
            region,
            categories,
            technologies,
            certs,
            days,
            buyer_index,
        ) in enumerate(OPPORTUNITIES, 1):
            ext = f"DEMO-2026-{index:03d}"
            existing = db.scalar(
                select(Opportunity).where(
                    Opportunity.source == "DEMO", Opportunity.external_id == ext
                )
            )
            values = dict(
                title=title,
                description=f"Synthetic procurement scenario for {title.lower()}. This record is demo data, not a live notice.",
                buyer_id=buyer_records[buyer_index].id,
                publication_date=today - timedelta(days=(index % 12) + 2),
                deadline=today + timedelta(days=days),
                estimated_value_min=Decimal(minimum),
                estimated_value_max=Decimal(maximum),
                categories=categories,
                technologies=technologies,
                certifications_required=certs,
                location=region,
                region=region,
                country="BE" if region == "Bruxelles" else "FR",
                contract_duration_months=12 + (index % 4) * 6,
                procedure_type="Open procedure",
                cpv_codes=[f"72{index:06d}"[:8]],
                raw_metadata={"fixture": True, "synthetic": True},
                is_demo=True,
            )
            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
                logger.info("duplicate_opportunity_updated external_id=%s", ext)
            else:
                db.add(Opportunity(source="DEMO", external_id=ext, **values))
        db.commit()
        target = db.scalar(
            select(Opportunity).where(
                Opportunity.source == "DEMO", Opportunity.external_id == "DEMO-2026-003"
            )
        )
        if target is None:
            raise RuntimeError("Synthetic tender-to-team opportunity was not seeded")
        gap_specs = [
            (GapType.security, "CRITICAL", "Cybersecurity", True, 8),
            (GapType.certification, "HIGH", "ISO 27001", True, 6),
            (GapType.skill, "HIGH", "French procurement expertise", False, 6),
            (GapType.reference, "MEDIUM", "Healthcare reference", False, 4),
        ]
        gaps: list[CapabilityGap] = []
        for gap_type, severity, capability, mandatory, weight in gap_specs:
            gap = db.scalar(
                select(CapabilityGap).where(
                    CapabilityGap.opportunity_id == target.id,
                    CapabilityGap.organization_id == org.id,
                    CapabilityGap.capability == capability,
                )
            )
            if gap is None:
                gap = CapabilityGap(
                    opportunity_id=target.id,
                    organization_id=org.id,
                    gap_type=gap_type,
                    severity=severity,
                    capability=capability,
                    mandatory=mandatory,
                    coverage_weight=weight,
                    provenance="SYNTHETIC_DEMO",
                    is_demo=True,
                )
                db.add(gap)
                db.flush()
            gaps.append(gap)
        work_post = db.scalar(
            select(WorkPost).where(
                WorkPost.organization_id == org.id,
                WorkPost.title == "Cybersecurity Architect for healthcare data bid",
            )
        )
        if work_post is None:
            work_post = WorkPost(
                organization_id=org.id,
                created_by=owner.id,
                opportunity_id=target.id,
                capability_gap_id=gaps[0].id,
                post_type=WorkPostType.bid_project,
                title="Cybersecurity Architect for healthcare data bid",
                summary="Join a synthetic tender team to close security architecture and ISO 27001 evidence gaps for a public healthcare data-platform bid.",
                location="Paris",
                remote_policy="HYBRID",
                required_skills=["Cybersecurity", "French procurement expertise"],
                required_certifications=["ISO 27001"],
                compensation_min=Decimal("850"),
                compensation_max=Decimal("1050"),
                contingent_on_award=True,
                is_demo=True,
            )
            db.add(work_post)
            db.flush()
        if not db.scalar(
            select(Invitation).where(
                Invitation.organization_id == org.id,
                Invitation.professional_profile_id == elena.id,
                Invitation.work_post_id == work_post.id,
            )
        ):
            db.add(
                Invitation(
                    organization_id=org.id,
                    professional_profile_id=elena.id,
                    work_post_id=work_post.id,
                    opportunity_id=target.id,
                    invited_by=owner.id,
                    message="Synthetic invitation to review the healthcare data-platform bid project.",
                    is_demo=True,
                )
            )
        db.commit()
        if not db.scalar(
            select(PipelineItem).where(PipelineItem.organization_id == org.id).limit(1)
        ):
            seeded_opportunities = list(
                db.scalars(
                    select(Opportunity)
                    .where(Opportunity.source == "DEMO")
                    .order_by(Opportunity.external_id)
                    .limit(3)
                )
            )
            stages = [PipelineStage.qualified, PipelineStage.review, PipelineStage.preparing]
            probabilities = [60, 30, 70]
            for opportunity, stage, probability in zip(
                seeded_opportunities, stages, probabilities, strict=True
            ):
                db.add(
                    PipelineItem(
                        organization_id=org.id,
                        opportunity_id=opportunity.id,
                        stage=stage,
                        value=opportunity_value(opportunity),
                        probability=probability,
                        next_action="Review qualification evidence",
                        notes="Synthetic demo pipeline item.",
                    )
                )
        if not db.scalar(
            select(Notification).where(Notification.organization_id == org.id).limit(1)
        ):
            db.add(
                Notification(
                    organization_id=org.id,
                    type="deadline",
                    severity="warning",
                    title="Two demo opportunities close within seven days",
                    message="Review the Revenue Radar closing-soon segment. Synthetic demo alert.",
                    entity_type="dashboard",
                )
            )
        db.commit()
        recalculate_matches(db, company)
        logger.info("seed_complete opportunities=%s", len(OPPORTUNITIES))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
