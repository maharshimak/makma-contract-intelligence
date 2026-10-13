# Architecture and implemented scope

Next.js company/opportunity/pipeline UI -> FastAPI identity/session/CSRF/RBAC -> domain scoring/qualification/network/procurement adapters -> SQLAlchemy/Alembic database.

Company onboarding, opportunity discovery and qualification, matching/scoring, pipeline updates, buyer intelligence, team access, saved searches/notifications, password identities and hashed session tokens.

## Modules inspected

- `apps/web/eslint.config.mjs`: source/module definitions inspected.
- `apps/web/next-env.d.ts`: source/module definitions inspected.
- `apps/web/next.config.ts`: source/module definitions inspected.
- `apps/web/vitest.config.ts`: source/module definitions inspected.
- `apps/web/vitest.setup.ts`: source/module definitions inspected.
- `apps/web/scripts/start-standalone.mjs`: source/module definitions inspected.
- `apps/web/lib/access.test.ts`: source/module definitions inspected.
- `apps/web/lib/access.ts`: authorizeArea.
- `apps/web/lib/api.ts`: apiBase, request, completeCompanyOnboarding.
- `apps/web/lib/completeness.test.ts`: source/module definitions inspected.
- `apps/web/lib/completeness.ts`: isPresent, companyCompleteness, score.
- `apps/web/lib/format.ts`: money, valueRange, daysLeft, dateLabel.
- `apps/web/lib/journey.test.ts`: source/module definitions inspected.
- `apps/web/lib/journey.ts`: journeyStageIndex.
- `apps/web/lib/server-api.ts`: request.
- `apps/web/lib/team.test.ts`: source/module definitions inspected.
- `apps/web/lib/team.ts`: proposedCoverage.
- `apps/web/lib/types.ts`: source/module definitions inspected.
- `apps/web/components/AddToPipelineButton.tsx`: AddToPipelineButton, add.
- `apps/web/components/ApplyButton.tsx`: ApplyButton, apply.
- `apps/web/components/AppShell.test.tsx`: source/module definitions inspected.
- `apps/web/components/AppShell.tsx`: AppShell, initials, handler, nav, logout, switchWorkspace.
- `apps/web/components/BoampIngestionButton.tsx`: BoampIngestionButton, ingest.
- `apps/web/components/CompanyForm.tsx`: CompanyForm, text, set, save.
- `apps/web/components/CompanyOnboardingForm.test.tsx`: source/module definitions inspected.
- `apps/web/components/CompanyOnboardingForm.tsx`: CompanyOnboardingForm, submit.
- `apps/web/components/ErrorState.tsx`: ErrorState.
- `apps/web/components/OpportunityTable.test.tsx`: source/module definitions inspected.
- `apps/web/components/OpportunityTable.tsx`: OpportunityTable.
- `apps/web/components/PipelineBoard.test.tsx`: source/module definitions inspected.
- `apps/web/components/PipelineBoard.tsx`: PipelineBoard, move.
- `apps/web/components/ProductJourney.tsx`: ProductJourney, ProductGuide.
- `apps/web/components/SavedSearchList.tsx`: SavedSearchList, remove.
- `apps/web/components/SaveSearchButton.test.tsx`: source/module definitions inspected.
- `apps/web/components/SaveSearchButton.tsx`: SaveSearchButton, save.
- `apps/web/components/TeamBuilder.tsx`: TeamBuilder, toggle, create.
- `apps/web/app/layout.tsx`: RootLayout.
- `apps/web/app/page.tsx`: MarketingHome.
- `apps/web/app/signup/page.test.tsx`: source/module definitions inspected.
- `apps/web/app/signup/page.tsx`: Signup, submit.
- `apps/web/app/professional/layout.tsx`: ProfessionalLayout.
- `apps/web/app/professional/page.tsx`: ProfessionalHub.
- `apps/web/app/opportunities/page.tsx`: OpportunitiesRedirect.
- `apps/web/app/opportunities/[id]/page.tsx`: Text, OpportunityDetail.
- `apps/web/app/login/page.test.tsx`: source/module definitions inspected.
- `apps/web/app/login/page.tsx`: LoginForm, submit, demo, Login.
- `apps/web/app/future/[feature]/page.tsx`: Future.
- `apps/web/app/forbidden/page.tsx`: ForbiddenPage.
- `apps/web/app/company/page.tsx`: CompanyRedirect.
- `apps/web/app/buyers/page.tsx`: BuyersRedirect.
- `apps/web/app/app/error.tsx`: AppError.
- `apps/web/app/app/layout.tsx`: ApplicationLayout.
- `apps/web/app/app/loading.tsx`: Loading.
- `apps/web/app/app/page.tsx`: AppHome.
- `apps/web/app/app/team-builder/[id]/page.tsx`: TeamBuilderPage.
- `apps/web/app/app/saved/page.tsx`: Saved.
- `apps/web/app/app/radar/page.tsx`: Dashboard.
- `apps/web/app/app/pipeline/page.tsx`: Pipeline.
- `apps/web/app/app/opportunities/page.tsx`: Opportunities.
- `apps/web/app/app/opportunities/[id]/page.tsx`: source/module definitions inspected.
- `apps/web/app/app/marketplace/page.tsx`: MarketplacePage.
- `apps/web/app/app/future/[feature]/page.tsx`: source/module definitions inspected.
- `apps/web/app/app/company/page.tsx`: CompanyPage.
- `apps/web/app/app/buyers/page.tsx`: Buyers.
- `apps/web/app/app/buyers/[id]/page.tsx`: BuyerDetail.
- `apps/web/app/app/alerts/page.tsx`: Alerts.
- `apps/web/app/admin/layout.tsx`: AdminLayout.
- `apps/web/app/admin/page.tsx`: AdminPage.
- `apps/api/tests/conftest.py`: override_db, database, client.
- `apps/api/tests/test_api.py`: test_health, test_company_read_and_update_recalculate, test_company_rejects_inverted_contract_range, test_listing_filtering_and_pagination, test_opportunity_detail_and_status, test_dashboard_and_buyers, test_pipeline_add_update_and_activity, test_saved_search_lifecycle_and_notifications.
- `apps/api/tests/test_auth.py`: _without_demo_header, test_unauthenticated_request_never_defaults_to_demo_user, test_company_signup_creates_owner_session_and_requires_csrf, test_professional_signup_has_no_company_permissions_and_can_login, test_workspace_switch_rejects_non_membership_and_admin_is_independent, test_duplicate_email_and_weak_password_are_rejected.
- `apps/api/tests/test_network.py`: test_demo_session_and_workspace_switching_are_membership_scoped, test_viewer_cannot_create_work_post, test_professional_marketplace_application_is_private_to_post_owner, test_tender_to_team_recommendations_and_draft, test_admin_route_is_independently_protected.
- `apps/api/tests/test_procurement.py`: FixtureAdapter, boamp_record, cleanup_boamp, test_boamp_adapter_fetch_and_normalize, test_ingestion_retains_raw_data_deduplicates_and_updates, test_procurement_admin_routes_are_protected, __init__, fetch_opportunities, fetcher.
- `apps/api/tests/test_qualification.py`: test_go_requires_strong_match_no_blockers_and_time, test_missing_requirement_makes_decision_conditional, test_expired_or_excluded_is_no_go.
- `apps/api/tests/test_scoring.py`: company, opportunity, buyer, test_perfect_match_is_high_priority, test_zero_or_excluded_match_is_low, test_missing_values_are_neutral_not_fabricated, test_below_and_above_range_are_penalized, test_partial_technology_overlap_and_geography_mismatch, test_missing_certification_is_explicit.
- `apps/api/tests/test_security_boundaries.py`: _anonymous, test_production_rejects_demo_and_insecure_cookie_configuration, test_invalid_and_expired_sessions_are_rejected, test_admin_access_matrix_uses_platform_role_only, test_signup_rejects_platform_role_payload_and_owner_stays_platform_user, test_removed_membership_and_cross_tenant_private_resources_are_blocked, test_targeted_notifications_are_private_and_org_notifications_are_shared, test_incomplete_workspace_exposes_onboarding_and_can_be_completed, test_untrusted_origin_is_rejected_on_login_and_signup.
- `apps/api/tests/test_seed.py`: test_seed_is_idempotent.
- `apps/api/app/auth.py`: Principal, _unauthenticated, current_principal, require_manager, require_platform_admin.
- `apps/api/app/auth_routes.py`: LoginWrite, SignupWrite, DemoLoginWrite, _slug, _set_session_cookies, _rate_limit, _require_trusted_origin, login, signup, logout, demo_login.
- `apps/api/app/auth_service.py`: NewSession, AuthRateLimiter, normalize_email, validate_password, hash_token, create_password_identity, verify_password_identity, create_session, __init__, check.
- `apps/api/app/bootstrap_admin.py`: main.
- `apps/api/app/config.py`: Settings, get_settings, cors_origin_list, validate_runtime_safety.
- `apps/api/app/database.py`: Base, get_db, enable_sqlite_foreign_keys.
- `apps/api/app/ingest.py`: main.
- `apps/api/app/main.py`: lifespan, security_headers, validation_error, health, company_or_404, get_company, get_company_by_id, create_company, complete_company_onboarding, update_company, list_opportunities, get_opportunity.
- `apps/api/app/models.py`: PipelineStatus, PipelineStage, PlatformRole, MembershipRole, WorkPostType, GapType, User, AuthIdentity, PasswordCredential, UserSession, ProfessionalProfile, Organization, OrganizationMember, CompanyProfile, Buyer, Opportunity, RawProcurementRecord, ProcurementIngestionRun, OpportunityMatch, PipelineItem, SavedSearch, Notification, ActivityEvent, WorkPost, Application, Invitation, CapabilityGap, BidTeam, BidTeamMember, AuditLog, utcnow.
- `apps/api/app/network.py`: _normalized, profile_strength, serialize_professional, serialize_work_post, create_work_post, create_application, serialize_application, opportunity_gaps, current_coverage, team_recommendations, create_bid_team.
- `apps/api/app/network_routes.py`: session, switch_workspace, workspaces, my_professional_profile, professionals, work_posts, post_work_post, apply, my_applications, post_applications, capability_gaps, recommendations.
- `apps/api/app/network_schemas.py`: WorkspaceRead, SessionRead, ProfessionalRead, WorkPostWrite, WorkPostRead, ApplicationWrite, ApplicationRead, CapabilityGapRead, TeamCandidateRead, TeamRecommendationRead, TeamMemberSelection, BidTeamWrite, BidTeamRead, AdminSummaryRead, validate_compensation.
- `apps/api/app/procurement.py`: SourceAdapter, IngestionResult, payload_hash, _date, _upsert_buyer, _opportunity_values, ingest_source, ingest_boamp, source_status, fetch_opportunities, normalize_opportunity.
- `apps/api/app/procurement_routes.py`: procurement_sources, run_boamp_ingestion.
- `apps/api/app/qualification.py`: QualificationResult, qualify_opportunity.
- `apps/api/app/schemas.py`: ApiModel, CompanyWrite, CompanyRead, BuyerRead, MatchRead, OpportunityRead, OpportunityPage, DashboardSummary, BuyerIntelligence, StatusUpdate, RecalculationResult, ErrorDetail, PipelineItemWrite, PipelineItemUpdate, PipelineItemRead, PipelineSummary, SavedSearchWrite, SavedSearchRead, NotificationRead, ActivityEventRead, QualificationRead, validate_contract_range.
- `apps/api/app/scoring.py`: ScoreResult, _norm, _overlap, priority_for, score_opportunity.
- `apps/api/app/seed.py`: seed.
- `apps/api/app/services.py`: recalculate_matches, opportunity_value, dashboard_metrics, serialize_match, serialize_opportunity.
- `apps/api/app/workflow.py`: add_pipeline_item, update_pipeline_item, pipeline_item, pipeline_items, serialize_pipeline_item, pipeline_summary, create_saved_search.
- `apps/api/app/__init__.py`: source/module definitions inspected.
- `apps/api/app/adapters/base.py`: NormalizedBuyer, NormalizedOpportunity, ProcurementSourceAdapter, FutureSourceAdapter, fetch_opportunities, normalize_opportunity, health_check, fetch_opportunities, normalize_opportunity, health_check.
- `apps/api/app/adapters/sources.py`: BoampAdapter, TedAdapter, ApprochAdapter, DecpAdapter, _fetch_json, _parse_datetime, _as_list, _text, _nested_json, _walk, _eforms_values, __init__, fetch_opportunities, normalize_opportunity, health_check.
- `apps/api/app/adapters/__init__.py`: source/module definitions inspected.
- `apps/api/alembic/env.py`: run_migrations_offline, run_migrations_online.
- `apps/api/alembic/versions/20260814_0001_initial.py`: upgrade, downgrade.
- `apps/api/alembic/versions/20260814_0002_workflow.py`: upgrade, downgrade.
- `apps/api/alembic/versions/20260814_0003_network_foundation.py`: upgrade, downgrade.
- `apps/api/alembic/versions/20260814_0004_boamp_ingestion.py`: upgrade, downgrade.
- `apps/api/alembic/versions/20260815_0005_production_auth.py`: upgrade, downgrade.

## Request routes

| Source | Method | Path | Handler |
|---|---|---|---|
| `apps/api/app/auth_routes.py` | post | `/login` | `login` |
| `apps/api/app/auth_routes.py` | post | `/signup` | `signup` |
| `apps/api/app/auth_routes.py` | post | `/logout` | `logout` |
| `apps/api/app/auth_routes.py` | post | `/demo-login` | `demo_login` |
| `apps/api/app/main.py` | get | `/health` | `health` |
| `apps/api/app/main.py` | get | `/api/company` | `get_company` |
| `apps/api/app/main.py` | get | `/api/company/{company_id}` | `get_company_by_id` |
| `apps/api/app/main.py` | post | `/api/company` | `create_company` |
| `apps/api/app/main.py` | post | `/api/company/onboarding` | `complete_company_onboarding` |
| `apps/api/app/main.py` | put | `/api/company/{company_id}` | `update_company` |
| `apps/api/app/main.py` | get | `/api/opportunities` | `list_opportunities` |
| `apps/api/app/main.py` | get | `/api/opportunities/{opportunity_id}` | `get_opportunity` |
| `apps/api/app/main.py` | get | `/api/opportunities/{opportunity_id}/qualification` | `get_qualification` |
| `apps/api/app/main.py` | post | `/api/opportunities/recalculate-matches` | `recalculate` |
| `apps/api/app/main.py` | patch | `/api/opportunities/{opportunity_id}/status` | `update_status` |
| `apps/api/app/main.py` | get | `/api/dashboard/summary` | `dashboard` |
| `apps/api/app/main.py` | get | `/api/buyers` | `buyers` |
| `apps/api/app/main.py` | get | `/api/buyers/{buyer_id}` | `buyer_detail` |
| `apps/api/app/main.py` | get | `/api/buyers/{buyer_id}/opportunities` | `buyer_opportunities` |
| `apps/api/app/main.py` | get | `/api/pipeline` | `get_pipeline` |
| `apps/api/app/main.py` | get | `/api/pipeline/summary` | `get_pipeline_summary` |
| `apps/api/app/main.py` | post | `/api/pipeline` | `create_pipeline_item` |
| `apps/api/app/main.py` | patch | `/api/pipeline/{item_id}` | `patch_pipeline_item` |
| `apps/api/app/main.py` | get | `/api/saved-searches` | `get_saved_searches` |
| `apps/api/app/main.py` | post | `/api/saved-searches` | `post_saved_search` |
| `apps/api/app/main.py` | delete | `/api/saved-searches/{search_id}` | `delete_saved_search` |
| `apps/api/app/main.py` | get | `/api/notifications` | `get_notifications` |
| `apps/api/app/main.py` | get | `/api/activity` | `get_activity` |
| `apps/api/app/network_routes.py` | get | `/session` | `session` |
| `apps/api/app/network_routes.py` | post | `/session/workspace` | `switch_workspace` |
| `apps/api/app/network_routes.py` | get | `/workspaces` | `workspaces` |
| `apps/api/app/network_routes.py` | get | `/professionals/me` | `my_professional_profile` |
| `apps/api/app/network_routes.py` | get | `/professionals` | `professionals` |
| `apps/api/app/network_routes.py` | get | `/work-posts` | `work_posts` |
| `apps/api/app/network_routes.py` | post | `/work-posts` | `post_work_post` |
| `apps/api/app/network_routes.py` | post | `/work-posts/{post_id}/applications` | `apply` |
| `apps/api/app/network_routes.py` | get | `/applications/me` | `my_applications` |
| `apps/api/app/network_routes.py` | get | `/work-posts/{post_id}/applications` | `post_applications` |
| `apps/api/app/network_routes.py` | get | `/opportunities/{opportunity_id}/capability-gaps` | `capability_gaps` |
| `apps/api/app/network_routes.py` | get | `/opportunities/{opportunity_id}/team-recommendations` | `recommendations` |
| `apps/api/app/network_routes.py` | post | `/opportunities/{opportunity_id}/bid-team` | `build_team` |
| `apps/api/app/network_routes.py` | get | `/admin/summary` | `admin_summary` |
| `apps/api/app/procurement_routes.py` | get | `/sources` | `procurement_sources` |
| `apps/api/app/procurement_routes.py` | post | `/boamp/ingest` | `run_boamp_ingestion` |

Static parsing found the modules/handlers above without importing/executing them. Fixtures, enums and abstract declarations are not proof that every flow is complete. See TECHNICAL_ISSUES.md for incomplete adapters and inconsistent pipeline contracts.
