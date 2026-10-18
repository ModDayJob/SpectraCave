# Privacy and local operation

SpectraCave reads chosen FITS folders locally. It does not edit original captures.
Results, derived spectra, imported response data and review prompts are written
under the app's `results/` folder. FITS headers and result evidence can contain
star names, filenames, observer/site information or other information you supplied.
Treat result exports as personal files and review them before sharing.

The server listens on loopback only. It is a single-user local application, not a
multi-user web service. Do not expose its port to a network. There are no user
accounts, analytics, advertising, telemetry or automatic observation uploads.
Browser preferences remember the observing folder, selected curves and reference.

First launch downloads Python dependencies from PyPI. External resource links
open their provider websites under those websites' own privacy policies.

Only the explicit AI-review action sends an evidence summary and sampled spectral
measurements to OpenAI using your key. Filenames are removed from the per-frame
checks and rejection list; raw images are not sent. Other evidence/provenance
metadata and user-supplied text can be included. Review source metadata before
using AI. The API request sets `store: false`; the provider's applicable policies
still govern processing and retention. API charges may apply. AI credentials are
read from the launch environment, not written into the browser or exported files.

No AAVSO login, API integration or uploads are implemented. Signing into AAVSO
in your browser does not provide SpectraCave with that session or its credentials.
