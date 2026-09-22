# Test-data provenance

## Synthetic corpus

`tools/crosscheck.py` creates 72 deterministic combinations (1/2 ports, RI/MA/DB, four frequency units, three real reference resistances), plus three repository samples and two analytic circuit examples. These 77 files are synthetic, not laboratory measurements. The seed is 20260922. Numerical tolerance is rtol=1e-10, atol=1e-12 for complex components; other field tolerances are explicit in the script.

## Public upstream-labelled measured examples

`tools/test_measured.py` reads the **unmodified** data bundled with the pinned `scikit-rf==1.8.0` test dependency. It checks the Git blob identity before comparing the entire parsed network and CSV export to scikit-rf. A missing file, version mismatch, hash mismatch or comparison failure fails the test; it is never silently skipped.

| File | Upstream description | Pinned Git blob |
| --- | --- | --- |
| `ring slot measured.s1p` | One-port ring-slot measurement example | `094aee842edea2e16af6003e5186406b0bccc9f1` |
| `ind.s2p` | Upstream describes a measured 1 nH series inductor with parasitics | `70234dfc515caaf98bd050da97520f1e0eb91b01` |

Source declarations: [scikit-rf v1.8.0 skrf/data/__init__.py](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/skrf/data/__init__.py).
Source files: [ring slot measured.s1p](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/skrf/data/ring%20slot%20measured.s1p), [ind.s2p](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/skrf/data/ind.s2p).

“Measured” here is **the upstream author's classification**, not an independent claim about instrumentation, calibration or measurement uncertainty. In particular, `ind.s2p` has an `SP1.SP block` export comment; we do not infer the acquisition hardware or claim to have repeated that measurement. Both fixtures may have been processed or re-exported. This is public-file compatibility testing, not metrology certification.

scikit-rf is [BSD-3-Clause licensed](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/LICENSE.txt). We do not copy its parser source or vendor its fixture bytes into the repository or offline application. The data remain in the installed upstream package during tests, with their upstream license. The generated report records per-file SHA256, Git blob, sample-derived complex-value count and numerical differences. It contains no user-uploaded measurement files.

## Reproduce

Build `dist/` first as described in the README, then:

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3
python tools/crosscheck.py
python tools/test_measured.py
```

Results are written separately to `verification/crosscheck.json` and `verification/measured-files.json`. Do not merge their counts into a claim that all tested files are real measurements. Large/extreme inputs, vendor extensions, physical mobile devices and other browsers remain outside these two datasets.
