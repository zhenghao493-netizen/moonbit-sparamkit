///|
/// Host glue only. The two callbacks run the MoonBit parser and report encoder.
extern "js" fn install(
  analyze : (String, Int) -> String,
  csv : (String, Int) -> String,
) -> Unit =
  #|(analyze, csv) => { globalThis.SParamKit = Object.freeze({ analyze, csv }); }

///|
fn main {
  install(@sparam.analyze_touchstone_json, @sparam.export_touchstone_csv_json)
}
