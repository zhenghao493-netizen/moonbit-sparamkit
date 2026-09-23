# Worker recovery — 0.1.0-rc.2

Verified 2026-09-23. Implementation: `d0cb8a5302386b437e59fe37235a262b3918753e`; tested PR checkout: `a0d66e7d71fb7a238f852600be1c9836cb5d507d`.

[PR #9](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/9) merged as `400ba78ca4c73adc1d6d55fc6fe7c8025fbc2890`. The comparison with the tested checkout returned no changed files. This note is a documentation-only follow-up.

## Fixes

Review of the rc.1 workbench reproduced two failure paths: a synchronous `postMessage` error left its 15-second deadline active, and a worker startup exception left subsequent requests using the failed worker.

The workbench now retires a failed worker, clears its pending deadlines, and creates a replacement on the next user action. Constructor failures release the Blob URL. Timeout handling does not attempt an immediate restart, and delayed events from an old worker cannot cancel a newer request. `messageerror` follows the same cleanup path.

Failed analysis preserves the input and enables retry. A CSV transport failure preserves the accepted dataset so the user can retry export without reloading the page. The MoonBit numerical core and public API are unchanged.

## Recovery tests

`tools/test_worker_recovery.py` covers eight scenarios: constructor failure, actual worker startup exception, synchronous send failure, CSV retry, message decoding failure, timeout followed by failed construction, a delayed error from a retired worker, and repeated constructor failures.

The tests alter only worker startup, transport, events and deadlines. Successful responses still come from the compiled MoonBit core. The timeout test invokes the real deadline callback deterministically instead of waiting 15 seconds.

Downloaded reports from the [platform run](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190132) show:

| Platform / browser | New recovery scenarios | Existing browser scenarios | Mode |
| --- | --- | --- | --- |
| Linux / Chromium 152.0.7977.0 | 8 passed | 30 passed | file |
| Linux / Firefox 141.0 | 8 passed | 30 passed | file |
| Linux / Playwright WebKit 26.0 | 8 passed | 30 passed | file |
| Windows / Chromium 140.0.7339.16 | 8 passed | 30 passed | file |

Each environment also passed the numeric-browser check and host tests. These are repeated executions of the same scenario suites. Playwright WebKit is the tested engine, not a branded Safari or physical mobile-device run. Local browser reproduction used an injected document; the actual file-mode results above are from GitHub Actions.

## Acceptance results

All five PR workflows passed:

- [Core: 35811190201](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190201): 104/104 tests per JS and wasm-gc backend, with format, type checks, builds and examples.
- [Source package: 35811190164](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190164): 74 source files, fresh extraction/rebuild, and identical member paths and bytes after repackaging.
- [Tool: 35811190171](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190171): existing numerical, public-file, browser and new recovery checks.
- [Platforms: 35811190132](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190132): four environments listed above.
- [Unified submission: 35811190139](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35811190139): all 23 command stages passed.

The submission's actual logs report 104 tests passed on each backend. Its reports also record 24 CLI checks, six file-I/O fault checks, ten distribution checks, 14 host groups, five independent consumer cases per backend, and the high-precision numerical comparison. The existing scikit-rf corpus of 77 synthetic files / 4,398 complex values and two pinned public files / 141 values passed again.

The delivered ZIP was downloaded, extracted and checked independently: all 127 payload hashes matched. Source files were compared with the reviewed implementation. No new measurement corpus was introduced in this iteration.

## Delivered files

Submission artifact `10730055647` contains `SParamKit-0.1.0-rc.2-submission.zip`.

- Submission ZIP SHA256: `c1051a4005410e3c39ad4b377b2aee198f1bf93fb42e0e94cbd469f0c3138666`.
- Source ZIP SHA256: `90a5417cc3a38032a889de010a7024543e252e8a0b8332921d294e7d56b0f475`.
- Compiled core SHA256: `bbca727057836d2a741f57d57cee80b0b3a8a25e52603493f9d4c8ac1f35cc56`, unchanged from rc.1.

The package manifest identifies the tested PR checkout. After extraction, open `workbench/index.html`; source and current reports are included alongside it. The submission artifact has 90-day retention and can be rebuilt with `tools/prepare_submission.py`.

Usage and recovery steps are in [GETTING_STARTED.md](../docs/GETTING_STARTED.md). The submitted one/two-port format scope is unchanged.
