# Scientific methods and limits

## Scientific limits

- Two-dimensional primary FITS HDUs are supported, with integer or floating pixel values. Compressed FITS, image extensions and cubes are not supported.
- ASI585 16-bit-mapped data use an inferred 65,520 clipping ceiling; other integer FITS use the format maximum. This is not a universal detector linearity calibration. Floating FITS need an independently supplied detector saturation model before clipping can be established.
- Bright-source selection and local tracking are not plate solving or catalog identification. Overlapping spectra can contaminate an aperture. Review crowded fields manually.
- Wavelength calibration remains provisional. There is no automatic line identification, absolute flux calibration, matched dark/flat correction, independent atmospheric correction, published-template fitting, numerical temperature fit, radial velocity or abundance inference. The calibration workspace can import a user-supplied relative response curve; it does not derive or validate that curve automatically.
- Repeatability statistics are dominated by broad spectral shape and are not chemical detection significance. No molecule or element is automatically marked confirmed.
- Tracking follows translations locally, not field rotation or arbitrary optical distortion. Default search range is 60 original pixels per exposure; larger jumps can select the wrong source or fail. Very low-signal traces require manual inspection.

## Tests and validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover unsigned FITS decoding, truncated headers/pixels, Bayer averaging, shifted synthetic spectra, clipping rejection, reference fitting and serialization of a successful analysis. Real-data validation used all 92 Aldebaran and all 30 Mirach light frames; their profiles correlate above 0.998 with the earlier one-off extractions. These checks validate implementation consistency, not physical calibration accuracy.

The server binds only to loopback. Local mutation requests require an unpredictable session token and matching Host header. Do not expose this development server to a network. Input FITS header strings are treated as observation data, not AI instructions.

## Chemical fingerprint display and colors

The chemistry panel screens selected laboratory regions for H, He I, Na I D, Mg I b, Ca II H/K and Ca I 422.67 nm. Laboratory air wavelengths link to NIST. Sodium D and magnesium b are explicitly shown as blended regions; helium/sodium and calcium/hydrogen ambiguities are noted. A local continuum screen searches ±4 nm for an extremum with at least 3% contrast relative to shoulder bands 8–14 nm away. Independent subsets must both show the same kind of feature within 3 nm for a repeatability label. These thresholds are heuristic, not statistical confidence, elemental detection significance, abundance, or a resolution measurement. A repeated peak is not automatically an emission line. Multiple reference regions can flag the same broad feature. Existing raw profiles can give different results from earlier hand-screened, smoothed extractions; neither constitutes a validated chemical detection.

No individual chemical identity is promoted to confirmed. Molecular template matching and fitted temperatures and velocities remain unimplemented. Relative response correction is available only through an explicitly imported user-supplied curve. The molecular panel states that limitation rather than inventing TiO bands.

The rainbow background and selected-star strip use an illustrative piecewise visible wavelength-to-sRGB map, 380–780 nm. Nonvisible wavelengths are neutral. Strip brightness is stretched from extracted intensity; it is not measured RGB, calibrated flux, photometry, or a true-color camera image. No meaningful rainbow is drawn without a wavelength scale. The visible-only plot filter defaults to 390–700 nm. Folder-watch choice and folder path are now preserved locally through browser reloads.

Run frontend scientific-screening tests with Node:

```sh
node tests/test_chemistry.cjs
```

## Rollover and detailed feature inspection

Hover over the spectrum graph or wavelength strip. Within 8 nm of a listed atomic guide, the tooltip shows the selected star, laboratory wavelength/region, nearby measured minimum, heuristic local depth, subset repeatability, blending warnings and unconfirmed identification status. This tolerance is a navigation aid, not a line-matching tolerance or uncertainty estimate. Outside those regions it explicitly reports that the small reference list does not cover all possible spectral features. The graph can show several stars; rollover uses **Star to inspect** when that curve is plotted, otherwise the first plotted curve, named in the tooltip.

Click near a guide to pin it. You can also use **Inspect a reference feature**, or activate a reference-table row with Enter/Space. The feature inspector provides a physical explanation, measured wavelength offset, local depth, photon energy at the laboratory wavelength and caveats. **Science details** adds the exact shoulder/search windows, the linear continuum procedure, independent-subset values and a continuum-normalized close-up.

The signed trapezoidal integral over the sampled ±4 nm search window is labeled **search-window absorption integral**, not a fitted full-line equivalent width. A finite window, structured continuum, blends and instrument response can strongly bias it. Negative values and negative depths are retained rather than forced into absorption claims. Photon energy uses E = hc/λ at the laboratory reference, not a fitted stellar temperature. Wavelength offsets are not converted to velocities. Absolute wavelength accuracy and instrumental resolving power remain unestablished. The zoom display clips relative flux to 0.4–1.6 and states that display range; original measurements are unaffected.

Atomic lines and blended regions are distinguished from molecular bands; no molecular-band rollover identities are fabricated without a validated template. Laboratory guides are references, not detected absorption bands.


## Guided calibration with research controls

The calibration workspace follows four steps: select an extracted reference, assign known lines, inspect and save, then apply to a derived copy. It never automatically marks line identities or chemical detections as validated.

- Select a completed extraction of a known reference star. The plot recovers original-pixel distance from the existing scale/offset, or uses pixel distances directly if uncalibrated. Choose a line row, then click the observed feature for an initial distance estimate; manually refine it if needed.
- Assign at least three distinct fit lines. Additional rows can be **held-out checks** or **excluded**. Check rows are not included in least squares. Component-blend entries in the reference list are only region guides: do not treat an unresolved blend center as an exact line centroid without a suitable model.
- Research controls offer an origin-constrained model (λ = a d) or a free-intercept model (λ = a d + b). Distances and wavelengths must be finite, positive, distinct in the fit and monotonically related. Fits are unweighted; no centroid uncertainties are supplied. The report includes per-line residuals, RMS, maximum error, same-spectrum held-out errors, leave-one-out predictions, scaled design-matrix condition number, degrees of freedom and the fit interval.
- Fit residuals are internal consistency diagnostics, not absolute accuracy. Held-out assignments from the same spectrum are not independent instrument validation. No acceptance threshold silently approves a fit.
- Save a named immutable JSON record under `results/calibrations/`. It includes the reference extraction ID, settings, chart hash, manual assignments, fit/check results, model and timestamp. Records reload after restarting the app. Download links expose only local results.
- Select a target and explicitly acknowledge the setup/transfer assumptions. Applying creates a new result with the parent extraction and calibration record referenced in provenance. The parent chart and FITS files remain unchanged. Samples outside the reference fit interval are counted and flagged as extrapolated.
- Optional CSV response curves have two columns: wavelength in nm and positive relative sensitivity, sorted strictly in wavelength. Provide the source and how it was obtained. The app normalizes sensitivity to its median over overlapping samples, divides the full/odd/even spectra, and crops uncovered wavelengths instead of extrapolating. It requires at least 20 overlapping samples. Coverage, source, curve hash and cropping are recorded. Relative flux is not absolute flux. Start from an uncorrected parent to prevent double correction or recalibration of already response-weighted flux.

This workspace does not derive a response from a published template, correct raw darks/flats or fit uncertainties. Those remain separate future improvements. Saved calibrations and imported response data are ignored by Git.

### Choose spectra and a comparison reference

The comparison list is built from completed extractions, including future results.
Use the checkboxes to show or hide individual runs; run IDs distinguish repeated
extractions of the same star. Choices are remembered in this browser. New runs
are selected automatically. Select all and Clear selection operate on the list.

Choose any extracted star as the **Comparison reference**. It remains selected
and its curve is drawn thicker and dashed. This is a visual reference only:
it does not confirm the star identity, fit a wavelength scale, divide spectra,
or apply an instrument-response correction. Clear selection also clears the
reference. Calibration remains in the separate calibration workspace.

- **Pixel distance** shows calibrated and uncalibrated runs together. Calibrated
  axes are inverted using their own scale and offset without changing saved data.
  This compares extraction geometry; equal pixel distances need not represent the
  same wavelength across setups or detector positions.
- **Wavelength** shows only selected runs with wavelength scales. Selected runs
  without a scale are explicitly listed as needing calibration. Laboratory guides
  and wavelength colors are available only in this view. A supplied scale may
  still be provisional; displaying it does not validate the calibration.

