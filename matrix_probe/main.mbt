// SPDX-License-Identifier: Apache-2.0

///|
struct PatternSlices {
  source : Array[Char]
  constants : Array[String]
  constraints : Array[String]
}

///|
extend PatternSlices with @syntax.IterVisitor::{base, visit_Impl}

///|
fn make_slices(source : String) -> PatternSlices {
  let chars : Array[Char] = []
  for ch in source.iter() {
    chars.push(ch)
  }
  { source: chars, constants: [], constraints: [] }
}

///|
fn PatternSlices::fragment(self, start : Int, end : Int) -> String {
  // Parser cnum counts Unicode scalar values, not UTF-16 string code units.
  let mut result = ""
  for i = start; i < end; i = i + 1 {
    result += "\{self.source[i]}"
  }
  result
}

///|
impl @syntax.IterVisitor for PatternSlices with fn visit_Pattern_Constant(
  self,
  c~,
  loc~,
) {
  ignore(c)
  self.constants.push(self.fragment(loc.start.cnum, loc.end.cnum))
}

///|
impl @syntax.IterVisitor for PatternSlices with fn visit_Pattern_Constraint(
  self,
  pat~,
  ty~,
  loc~,
) {
  self.constraints.push(self.fragment(loc.start.cnum, loc.end.cnum))
  @syntax.IterVisitor::visit_Pattern_Constraint(self.base(), pat~, ty~, loc~)
}

///|
fn inspect_patterns(source : String, engine : Int) -> String {
  @basic.show_loc.protect(String, fn() {
    let (impls, diagnostics) = if engine == 2 {
      let parsed = @cst.parse_structure(source, name="case.mbt")
      let reports : Array[@basic.Report] = []
      for diagnostic in parsed.diagnostics_view() {
        reports.push(diagnostic)
      }
      let (impls, lowered) = parsed.to_impls()
      for diagnostic in lowered {
        reports.push(diagnostic)
      }
      (impls, reports)
    } else {
      let parser : @parser.Parser = if engine == 0 { Handrolled } else { MoonYacc }
      @parser.parse_string(source, name="case.mbt", parser~)
    }
    let slices = make_slices(source)
    for impl_ in impls {
      slices.visit_Impl(impl_)
    }
    let result : Json = {
      "ast": ToJson::to_json(impls.map(impl_ => impl_.json_repr())),
      "diagnostics": ToJson::to_json(diagnostics),
      "constants": ToJson::to_json(slices.constants),
      "constraints": ToJson::to_json(slices.constraints),
    }
    result.stringify()
  })
}

///|
extern "js" fn install(inspect : (String, Int) -> String) -> Unit =
  #|(inspect) => { globalThis.ParserCheckMatrix = Object.freeze({ inspect }); }

///|
fn main {
  install(inspect_patterns)
}
