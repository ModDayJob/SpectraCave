# Public beta QA — 2026-10-18

Release: SpectraCave 0.3.0-beta.1. Scope: single-user local Python desktop workflow.

## Verified

- 19 Python unit tests: FITS decoding/truncation, Bayer averaging, synthetic trace
  tracking and saturation, calibration fitting/application, parent preservation,
  AI request/error mocks, pasted folder paths and malformed/local-auth requests.
- Real HTTP smoke: host/token enforcement, folder discovery, preview, successful
  extraction, calibration save/apply, CSV retrieval and unchanged source hashes.
- JavaScript chemistry and comparison suites, plus syntax checks.
- Clean virtual environment creation and dependency installation, readiness check,
  successful tests in the fresh runtime, and friendly occupied-port handling.
- Automated matrix on macOS, Windows and Linux with Python 3.10 and 3.12.
  Final run status is available in the repository's Actions tab.
- macOS browser flow on synthetic captures: two named extractions, dynamic curve
  selection, reference selection, pixel/wavelength notices, blank-row validation,
  calibration fit/save/transfer acknowledgement, derived copy and restart restore.
- No browser error logs during the verified flow. Layout checked at desktop width
  and 390px; this is a desktop-first app, not a mobile scientific-plot release.
- Source download is built from the clean repository's tracked files only.
  No personal observing data, generated results, private development history,
  virtual environments or credentials are included. SHA-256 accompanies the ZIP.

## Limits of this QA

Synthetic tests establish implementation behavior, not physical wavelength
accuracy or chemical identification. Broad instrument validation remains future
work. macOS received interactive browser and installer-path checks; Windows/Linux
received automated pipeline/HTTP checks, not hands-on native-launcher QA.

AI is optional and covered with mocked API responses; live paid AI review is not
certified. AAVSO import, authentication and compliant submission export are absent.
There are no automatic scientific confirmations or uploads. No hosted deployment,
account security, code signing or native installer is claimed.

## Feedback and rollback

Report reproducible issues through GitHub Issues without credentials or private
observing files. To roll back, stop the app, keep a backup of `results/`, and
restore your previous app folder. Never overwrite original capture folders.
