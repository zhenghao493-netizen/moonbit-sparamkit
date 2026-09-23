#!/usr/bin/env python3
"""Build a separate MoonBit application against a local source dependency."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MAIN = r'''///|
fn main {
  let source = "# Hz S RI R 50\n1 .3 -.4\n2 0 0\n"
  let report = @sparam.analyze_touchstone_json(source, 1)
  if !@json.valid(report) { abort("Expected valid JSON") }
  println(report)
}
'''
TESTS = r'''///|
test "consumer can parse and query one-port data" {
  let net = @sparam.parse_touchstone("# MHz S RI R 75\n100 .3 -.4", 1).unwrap()
  assert_true(net.ports == 1 && net.reference_ohms == 75.0)
  assert_true(net.samples[0].frequency_hz == 100000000.0)
  assert_true(net.source_format == @sparam.RI)
  let s = net.get_s(0, 1, 1).unwrap()
  assert_true(s.re == 0.3 && s.im == -0.4)
  assert_true((s.magnitude() - 0.5).abs() < 1.0e-12)
}

///|
test "consumer uses asymmetric two-port indexing" {
  let net = @sparam.parse_touchstone("# Hz S RI R 50\n1 .1 0 .2 0 .3 0 .4 0", 2).unwrap()
  assert_true(net.get_s(0, 2, 1).unwrap().re == 0.2)
  assert_true(net.get_s(0, 1, 2).unwrap().re == 0.3)
  assert_true(net.get_s(0, 0, 1) is None)
}

///|
test "consumer handles positioned errors and limit argument" {
  match @sparam.parse_touchstone("# Hz S RI R 50\n1 bad 0", 1) {
    Ok(_) => fail("Expected invalid field")
    Err(e) => {
      assert_true(e.code == @sparam.InvalidNumber)
      assert_true(e.line == 2 && e.column == 3)
    }
  }
  match @sparam.parse_touchstone("# Hz S RI R 50\n1 0 0\n2 0 0", 1, max_samples=1) {
    Ok(_) => fail("Expected sample limit")
    Err(e) => assert_true(e.code == @sparam.SampleLimit)
  }
}

///|
test "consumer can export and read versioned reports" {
  let text = "# Hz S RI R 50\n1 .3 -.4"
  let csv = @sparam.parse_touchstone(text, 1).unwrap().to_csv()
  assert_true(csv.has_prefix("frequency_hz,reference_ohms"))
  assert_true(csv.contains("1,50,1,1,0.3,-0.4"))
  guard @json.parse(@sparam.export_touchstone_csv_json(text, 1)) is Object(fields) else { fail("Expected object") }
  assert_true(fields.get("csv") is Some(String(value)) && value == csv)
}

///|
test "consumer observes undefined zero metrics" {
  let zero = @sparam.parse_touchstone("# Hz S RI R 50\n1 0 0", 1).unwrap().get_s(0, 1, 1).unwrap()
  assert_true(zero.magnitude_db() is None)
  assert_true(zero.phase_degrees() is None)
  let report = @sparam.analyze_touchstone_json("# Hz S RI R 50\n1 0 0", 1)
  assert_true(@json.valid(report) && report.contains("null"))
}
'''


def main() -> int:
    report = {'status':'failed', 'commands':[]}
    def run(args, cwd):
        p = subprocess.run(args, cwd=cwd, text=True, encoding='utf-8', errors='replace',
                           capture_output=True, timeout=180)
        report['commands'].append({'command':args, 'exit_code':p.returncode,
                                   'stdout':p.stdout, 'stderr':p.stderr})
        if p.returncode:
            raise RuntimeError(f'{args}\n{p.stdout}\n{p.stderr}')
        return p.stdout
    try:
        version = tomllib.loads((ROOT/'moon.mod').read_text(encoding='utf-8'))['version']
        with tempfile.TemporaryDirectory(prefix='sparamkit-consumer-') as temp:
            work = Path(temp)/'独立项目 with spaces'; work.mkdir()
            library, app = work/'library', work/'client'
            library.mkdir(); app.mkdir()
            # Copy only the public library source and metadata, not its tests or hosts.
            for file in ROOT.glob('*.mbt'):
                if not file.name.endswith(('_test.mbt', '_wbtest.mbt')):
                    shutil.copyfile(file, library/file.name)
            for name in ('moon.mod', 'moon.pkg', 'pkg.generated.mbti', 'LICENSE'):
                shutil.copyfile(ROOT/name, library/name)
            (work/'moon.work').write_text('members = ["library", "client"]\n', encoding='utf-8')
            (app/'moon.mod').write_text('name = "example/sparamkit-client"\nimport { "ttxiangshang/sparamkit@'+version+'" }\n', encoding='utf-8')
            (app/'moon.pkg').write_text('import {\n  "ttxiangshang/sparamkit" @sparam,\n  "moonbitlang/core/json",\n}\npkgtype(kind: "executable")\n', encoding='utf-8')
            (app/'main.mbt').write_text(MAIN, encoding='utf-8')
            (app/'client_wbtest.mbt').write_text(TESTS, encoding='utf-8')
            results = []
            for target in ('js','wasm-gc'):
                for verb in ('check','build','test'):
                    output = run(['moon',verb,'.','--target',target,'--deny-warn'], app)
                    if verb == 'test' and 'Total tests: 5, passed: 5, failed: 0.' not in output:
                        raise RuntimeError('Unexpected external test summary: '+output)
                result = json.loads(run(['moon','run','.','--target',target,'--deny-warn'], app))
                if not result.get('ok') or result['sample_count'] != 2 or result['samples'][0]['values'][0]['magnitude'] != 0.5:
                    raise RuntimeError('External application produced incorrect report')
                results.append({'target':target,'tests':5,'passed':5,'example_samples':2})
        report.update(status='passed', local_workspace=True, targets=results)
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    (ROOT/'verification').mkdir(exist_ok=True)
    (ROOT/'verification/consumer-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'commands'},ensure_ascii=False,indent=2))
    return 0 if report['status']=='passed' else 1


if __name__ == '__main__':
    sys.exit(main())
