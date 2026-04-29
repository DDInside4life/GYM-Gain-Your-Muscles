# Production Upgrade Changelog (2026-04-29)

## Step 1
- Introduced unified API error model with `error_code`, `message`, `context`.
- Mapped backend exceptions and validation errors to stable error contracts.
- Updated frontend API client to show user-friendly messages from error codes.

## Step 2
- Added persistent idempotency handling for:
  - `POST /workouts/regenerate`
  - `POST /workouts/{plan_id}/finalize-test-week`
  - `POST /workouts/sets`
- Added request fingerprint checks and conflict protection for key reuse.

## Step 3
- Added explicit atomic commit/rollback boundary for critical write flows.
- Ensured idempotency records and domain mutations are committed consistently.

## Step 4
- Added explainability payload for workout prescriptions:
  - reason for chosen load
  - target `%1RM`
  - derived e1RM basis
- Exposed explainability in workout runner UI via "Почему такой вес?".

## Step 5
- Improved adaptive autodeload using trend signals:
  - e1RM drop trend
  - high effort trend
  - missed session trend
- Preserved scheduled deload fallback for backward compatibility.

## Step 6
- Added compliance-aware plan adjustment with safeguards:
  - volume/intensity caps under persistent low compliance
  - bounded set/intensity changes to avoid over-correction

## Step 7
- Added structured request logs with:
  - `request_id`, `user_id`, `plan_id`, `endpoint`, `duration_ms`, `error_code`
- Added core product metrics:
  - generation success rate
  - finalize success rate
  - set-log average latency

## Step 8
- Added API contract tests for error and explainability payloads.
- Completed e2e smoke flow:
  - questionnaire -> generate -> log set -> finalize.

## Step 9
- Ran full backend test suite and frontend production build.
- Rebuilt docker stack and verified healthy services.
