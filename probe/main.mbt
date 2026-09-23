// SPDX-License-Identifier: Apache-2.0

///|
fn analyze(source : String, engine : Int, locations : Bool) -> String {
  let style : @basic.LocStyle = if locations { String } else { Hidden }
  @basic.show_loc.protect(style, fn() {
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
    let ast : Array[Json] = []
    for impl_ in impls {
      ast.push(impl_.json_repr())
    }
    let result : Json = {
      "ast": ToJson::to_json(ast),
      "diagnostics": ToJson::to_json(diagnostics),
    }
    result.stringify()
  })
}

///|
extern "js" fn install(parse : (String, Int, Bool) -> String) -> Unit =
  #|(parse) => { globalThis.ParserCheck = Object.freeze({ parse }); }

///|
fn main {
  install(analyze)
}
