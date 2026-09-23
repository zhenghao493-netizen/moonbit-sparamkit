#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compare a small valid-syntax corpus with both upstream parsers and mooninfo."""
from pathlib import Path
import argparse, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]

def first_difference(a, b, path='$'):
    if type(a) is not type(b):
        return {'path':path, 'reference':a, 'actual':b}
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return {'path':path, 'reference_keys':list(a), 'actual_keys':list(b)}
        for key in a:
            delta=first_difference(a[key],b[key],path+'.'+key)
            if delta:return delta
    elif isinstance(a, list):
        if len(a)!=len(b):return {'path':path,'reference_length':len(a),'actual_length':len(b)}
        for i,(x,y) in enumerate(zip(a,b)):
            delta=first_difference(x,y,f'{path}[{i}]')
            if delta:return delta
    elif a!=b:return {'path':path, 'reference':a, 'actual':b}
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('upstream',type=Path);args=ap.parse_args()
    upstream=args.upstream.resolve();out=ROOT/'reports/pilot';out.mkdir(parents=True,exist_ok=True)
    cases=json.loads((ROOT/'fixtures/pilot.json').read_text(encoding='utf-8'))
    probe=upstream/'parsercheck_probe'
    if probe.exists():raise RuntimeError('Refusing to overwrite parsercheck_probe')
    report={'status':'blocked','cases':[], 'target':'js'}
    try:
        expected_commit=json.loads((ROOT/'upstream.lock.json').read_text(encoding='utf-8'))['commit']
        if (upstream/'.git').exists():
            actual_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()
            if actual_commit!=expected_commit:raise RuntimeError('Unexpected upstream commit')
        report['upstream_commit']=expected_commit
        valid=[]
        for case in cases:
            name=case['name']
            if not name.replace('_','').isalnum():raise ValueError('Unsafe fixture name')
            source=out/(name+'.mbt');source.write_text(case['source'],encoding='utf-8')
            ref=out/(name+'.reference.json');ref.unlink(missing_ok=True)
            proc=subprocess.run(['mooninfo','-dump-ast',str(source),'-o',str(ref)],capture_output=True,text=True,timeout=20)
            (out/(name+'.reference.stderr')).write_text(proc.stderr,encoding='utf-8')
            if proc.returncode or not ref.is_file():raise RuntimeError('Reference execution failed: '+name)
            ast=json.loads(ref.read_text(encoding='utf-8'))
            if ast['has_parse_error'] or ast['has_deprecated_syntax']:
                raise RuntimeError('Fixture not eligible under contribution rules: '+name)
            valid.append((case,ast['impls']))
        probe.mkdir();(probe/'moon.pkg').write_text('import {\n  "moonbitlang/parser" @parser,\n  "moonbitlang/core/json",\n}\npkgtype(kind: "executable")\n',encoding='utf-8')
        inputs=',\n'.join('    ('+json.dumps(c['name'])+', '+json.dumps(c['source'],ensure_ascii=False)+')' for c,_ in valid)
        program='''///|
struct Outcome {
  case_name : String
  engine : String
  diagnostic_count : Int
  ast : Array[Json]
} derive(ToJson)

///|
fn main {
  let cases : Array[(String, String)] = [
'''+inputs+'''
  ]
  let engines : Array[(@parser.Parser, String)] = [
    (@parser.Handrolled, "handrolled"),
    (@parser.MoonYacc, "moonyacc"),
  ]
  for (case_name, source) in cases {
    for (parser, engine) in engines {
      let (impls, diagnostics) = @parser.parse_string(source, parser~)
      let ast : Array[Json] = []
      for impl_ in impls { ast.push(impl_.json_repr()) }
      let result = Outcome::{ case_name, engine, diagnostic_count: diagnostics.length(), ast }
      println(result.to_json().stringify())
    }
  }
}
'''
        (probe/'main.mbt').write_text(program,encoding='utf-8');(out/'probe.mbt').write_text(program,encoding='utf-8')
        p=subprocess.run(['moon','run','parsercheck_probe','--target','js','--release'],cwd=upstream,capture_output=True,text=True,encoding='utf-8',timeout=300)
        (out/'probe.stdout').write_text(p.stdout,encoding='utf-8');(out/'probe.stderr').write_text(p.stderr,encoding='utf-8')
        if p.returncode:raise RuntimeError('Probe failed; inspect probe.stderr')
        actual=[json.loads(line) for line in p.stdout.splitlines() if line.startswith('{')]
        if len(actual)!=2*len(valid):raise RuntimeError('Unexpected result count')
        seen=set();expected={c['name']:ast for c,ast in valid}
        for result in actual:
            key=(result['case_name'],result['engine'])
            if key in seen or key[0] not in expected or key[1] not in ('handrolled','moonyacc'):raise RuntimeError('Unexpected/duplicate probe result')
            seen.add(key)
            diff=first_difference(expected[key[0]],result['ast'])
            report['cases'].append({'name':key[0], 'engine':key[1], 'diagnostic_count':result['diagnostic_count'],
                                    'matches_reference':diff is None and result['diagnostic_count']==0, 'first_difference':diff})
        report['status']='matched' if all(c['matches_reference'] for c in report['cases']) else 'differences_found'
        report['inputs']=len(valid)
        report['comparisons']=len(report['cases'])
    except Exception as e:
        report['error']=str(e)
    finally:
        if probe.exists():shutil.rmtree(probe)
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='matched' else 1

if __name__=='__main__':sys.exit(main())
