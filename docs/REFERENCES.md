# Reference sources

Reviewed 2026-09-22. This project independently implements its documented subset; it is not a port of an upstream parser.

- [IBIS Touchstone 2.0 specification](https://ibis.org/touchstone_ver2.0/touchstone_ver2_0.pdf): explicitly identified Version 1.0 clauses used for syntax, line endings, option line and legacy network order. No implication of 2.0 implementation. Differences are recorded in [COMPATIBILITY.md](COMPATIBILITY.md).
- [Keysight SnP file format](https://helpfiles.keysight.com/csg/N1930xB/FilePrint/SnP_File_Format.htm): format descriptions and numerical representations.
- [MoonBit build tutorial](https://docs.moonbitlang.com/en/latest/toolchain/moon/tutorial.html), [commands](https://docs.moonbitlang.com/en/latest/toolchain/moon/commands.html), [official download](https://www.moonbitlang.com/download/): compiler, formatting, API generation and packaging.
- MoonBit core [string](https://github.com/moonbitlang/core/blob/main/string/pkg.generated.mbti), [math](https://github.com/moonbitlang/core/blob/main/math/pkg.generated.mbti), [builtin](https://github.com/moonbitlang/core/blob/main/builtin/pkg.generated.mbti): API signatures.
- [scikit-rf v1.8.0](https://github.com/scikit-rf/scikit-rf/tree/v1.8.0): independently executed test oracle, never runtime dependency or copied parser source. [BSD-3-Clause license](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/LICENSE.txt).
- scikit-rf [sample declarations](https://github.com/scikit-rf/scikit-rf/blob/v1.8.0/skrf/data/__init__.py) and two unchanged sample files: accessed only through the installed test dependency, not vendored. Exact content identities, qualifications and reproduction are in [TEST_DATA.md](TEST_DATA.md).

Independent synthetic and public-file tests, formatting and source-package reconstruction have separate gates and machine-readable results. See [verification/HARDENING.md](../verification/HARDENING.md) for precise tested commits; a reference URL does not itself establish test success or full conformance.
