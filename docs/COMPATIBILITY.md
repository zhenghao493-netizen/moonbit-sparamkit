# Touchstone compatibility matrix

Scope: `0.1.0-dev.4`, one/two-port single-ended S parameters. This is an implementation contract, **not full Touchstone conformance**.

Reference: [IBIS Touchstone 2.0 specification](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf), specifically its explicit **Version 1.0** rules: general syntax (printed p.4), option line (pp.6–7), network records/order (pp.12–14), noise data (pp.23–25). Using those legacy clauses does not imply support for version-2 keywords. The source implementation and tests decide current behaviour; differences below are intentional and visible.

| Feature | Current behaviour | Evidence / category |
| --- | --- | --- |
| One/two ports | Caller supplies 1 or 2; other counts rejected | `core_wbtest.mbt`: port count, wire order |
| S11/S21/S12/S22 order | Uses legacy column order, not row-major | Asymmetric values in unit and independent tests |
| Frequency units | Hz, kHz, MHz, GHz; normalize to Hz | Unit tests and 72 generated combinations |
| Representations | RI, MA, DB; angles in degrees; DB uses divisor 20 | Unit and independent numerical tests |
| Option defaults | Single `#` means GHz/S/MA/50 ohms | Option-default test |
| Option case/order | Case-insensitive; categories may be reordered, R keeps its value | All 24 category permutations tested |
| Positive real reference | Common finite positive resistance for both ports | Reference validation tests |
| LF/CRLF/CR line endings | All accepted, including mixtures; errors retain physical line number | `compatibility_wbtest.mbt` |
| Comments/blank lines | `!` to physical end of line; ordinary prose ignored, reserved impedance declarations checked | Comment/line-ending tests |
| Scientific notation | Decimal with e/E, sign, optional decimal point | Grammar and range tests |
| Duplicate option line | Rejected, rather than ignored | **Stricter policy**: specification says subsequent option lines are ignored |
| Repeated option category | Rejected rather than last-value-wins | **Stricter policy** |
| Record continuation | A frequency record may span lines; each new record begins on a new line | **Compatibility extension** to the legacy single-line description; eight split positions tested |
| Initial BOM | One leading U+FEFF accepted; embedded/repeated markers rejected | **Encoding extension**, not part of the ASCII specification; BOM counts as one source column |
| Non-ASCII content | UTF-8 comment text permitted; numeric fields remain ASCII decimal | **Encoding extension**; not a validator of the standard's ASCII-only restriction |
| Frequencies | Nonnegative and strictly increasing; no automatic sort/deduplication | Negative/duplicate/order tests; explicit implementation restriction |
| Precision | IEEE binary64; overflow and nonzero-decimal underflow to zero rejected | **Implementation limit**, not arbitrary precision |
| Zero magnitude | Finite dB and phase unavailable; JSON `null` | Unit and browser tests |
| 2.0 keywords/mixed mode | Bracketed keyword sections rejected | `UnsupportedVersion`; no 2.0 conformance claim |
| More ports, Y/Z/H/G | Rejected | `UnsupportedPorts` / `UnsupportedParameter` |
| Noise records | Not parsed or discarded; standard five-field blocks do not form supported records | May return field-count/order error rather than a noise-specific code |
| Recognized impedance comments | Standalone `! Port Impedance` followed by one real/imaginary pair per port, after header, on one line; every real part must equal header R exactly and every imaginary part must be zero | **Narrow safety guard**: conflicts, invalid numbers, ambiguous placement, truncated/multiline/matrix forms return `UnsupportedMetadata`; never renormalizes S |
| Other vendor metadata | Still not interpreted (including Gamma); unknown labels can remain ordinary comments | No general HFSS/vendor compatibility claim; re-export using a common real reference if the file depends on unsupported metadata |
| Input budgets | Core: 8 Mi code units / 100000 samples; report: 2 Mi / 20000; files: 2 MiB | Explicit resource policies; all checked before returning results |
| Visualization | Principal phase only; no line across wrap; logarithmic axis omits 0 Hz visually only | Browser tests; exports retain all data |

`moon test` exercises the documented contract, not every possible standard-compliant input. `tools/crosscheck.py` compares the supported common subset, not the whole standard. Two upstream-labelled measured fixtures are separately tracked in [TEST_DATA.md](TEST_DATA.md); they do not demonstrate arbitrary instrument compatibility.

The `Port` and `Impedance` labels are case-insensitive, separated by horizontal ASCII whitespace. This label is reserved: prose starting with those two words may be rejected as malformed metadata. Numeric comparisons are exact after binary64 conversion; no tolerance silently treats different impedances as equal. This is not full vendor-metadata support or impedance renormalization.
