# Changelog

All notable changes to PrivacyOps Africa Core are documented here.

## [0.2.0] - 2026-05-28

### Added

- Admin API module for system settings, background jobs, system health, and integration error visibility.
- `system_settings` and `background_jobs` database tables.
- Framework pack import/export and review-state update APIs.
- Data inventory enhancements: update, delete, search/filter, and export (`CSV`, `JSON`, `PDF`).
- Frontend admin panel route and controls for AI module setting and ops visibility.

### Changed

- Renamed API branding to PrivacyOps Africa Core.
- AI assistant now enforced as opt-in per organization and disabled by default.
- Framework version model now tracks review status, notes, and source reference.

### Testing

- Added tests for framework pack lifecycle and admin AI-gating workflow.
- Added tests for processing activity update/delete/export behavior.
