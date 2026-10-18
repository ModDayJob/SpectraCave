# SpectraCave beta guide

**Explore the science hidden in starlight.**

SpectraCave is a free-for-noncommercial-use, local spectroscopy workbench for
amateur astronomers. Extract spectra from FITS captures, compare selected stars
and a reference, explore candidate absorption/emission features, and export the
measurement evidence. Advanced controls stay tucked away until needed.

**Public beta 0.3.0-beta.1.** This is a downloadable Python app, not a hosted
website or a signed native installer. Your original FITS captures are read only.

## Get started

1. Download the ZIP from [Releases](https://github.com/ModDayJob/SpectraCave/releases/tag/v0.3.0-beta.1)
   and extract it into a folder you can write to. Do not run it inside the ZIP.
2. Install **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/).
   On Windows, enable the Python launcher during installation.
3. Start the app:
   - **macOS:** open `Launch.command`, or run `python3 start.py` in its folder.
   - **Windows:** open `Start.bat`, or run `py -3 start.py` in its folder.
   - **Linux:** run `python3 start.py` in its folder.
4. On first launch, it creates a private `.venv` and installs NumPy and Pillow
   from PyPI. Internet is required for that setup. Then your browser opens locally.
5. Keep the terminal open. Stop the app with Control-C. Later launches reuse the
   environment. To choose another port: `python3 start.py --port 8875`.

If your computer blocks downloaded scripts, use the documented Python command
from a terminal; review the source and your computer's policy first.

## Your first spectrum

1. Paste the folder containing your FITS captures and choose **Find captures**.
   Subfolders are included. Plain, quoted and shell-escaped paths are supported.
2. Choose a capture group. Click the white, undispersed image of your star,
   then give the extraction a useful name.
3. Open **Adjust extraction settings** and check direction, slope and distance
   range. Initial values are examples, not automatically detected equipment settings.
   Use original sensor pixels. Leave the wavelength scale blank unless you have
   a justified reference calibration.
4. Choose **Measure this star**. Only one extraction runs at a time. The app
   reports usable/rejected exposures and saves results under `results/`.
5. Use the comparison checkboxes to choose curves. Select a reference for a
   thicker dashed curve. Pixel view includes uncalibrated results; wavelength
   view explains which selections need calibration.

Folder watching refreshes the capture list; it does not automatically analyze,
operate ASIAIR, move a telescope or send data online. Completed results survive
restarts. Back up `results/` before replacing the app folder during an update.

## What the beta can and cannot tell you

- Supports uncompressed 2-D primary FITS images. Cubes, compressed FITS and
  reduced 1-D reference spectra are not supported yet.
- Initially developed with an ASI585MC and SA200. Other compatible FITS can be
  read, but broad camera/grating validation and equipment profiles remain future work.
- Calibration is observer-assigned and provisional. A good residual alone does
  not verify a line assignment. No target identity is independently catalog matched.
- Chemical guides and repeatable dip/peak candidates are **not confirmed species**.
  The beta does not measure elemental percentages, temperature or radial velocity.
- Raw dark/flat correction, published-template matching and absolute flux
  calibration are not implemented. Optional imported response curves remain
  the observer's responsibility.
- Rainbow colors are illustrative wavelength colors, not measured true color.

See [SCIENCE.md](../SCIENCE.md) for methods, thresholds and limitations.

## AAVSO

The app links to AVSpec searches, approved standards and submission guidance.
**AAVSO API connection, 1-D reference FITS import and submission-ready FITS export
are not implemented in this beta.** CSV/JSON exports must not be submitted as if
AAVSO-compliant. No AAVSO credentials or data are bundled. A browser login does
not connect the app to an API. AAVSO is not affiliated with or endorsing this app.

## Optional AI review

Local analysis is free and works without an AI account. AI review is optional
and may incur your provider's API charges. Set `OPENAI_API_KEY` and optionally
`OPENAI_MODEL` in the launch environment; `.env` files are not automatically loaded.
The explicit review button sends numerical evidence and sampled profiles to
OpenAI. Original images are not sent. Review uses one AI model organized into
three perspectives, not human expert sign-off. No background AI calls run.
See [PRIVACY.md](../PRIVACY.md).

## Feedback and license

Report bugs with your operating system, Python version, steps and any error text
in [Issues](https://github.com/ModDayJob/SpectraCave/issues). Do not post credentials,
private headers or original observing files unless you intend to share them.

Licensed under [PolyForm Noncommercial 1.0.0](../LICENSE). Free noncommercial use;
see the license for its exact permissions. This is source-available software,
not unrestricted open source. Optional donations are welcome; there is no
payment requirement or in-app payment collection.
