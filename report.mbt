///| Encode only finite values: undefined phase and dB must be JSON null.
fn report_number(value : Double?) -> Json {
  match value {
    Some(number) if finite(number) => @json.to_json(number)
    _ => null
  }
}

///|
fn report_error(error : Diagnostic) -> String {
  let result : Json = {
    "schema_version": @json.to_json(1),
    "ok": @json.to_json(false),
    "error": {
      "code": @json.to_json(@debug.to_string(error.code)),
      "line": @json.to_json(error.line),
      "column": @json.to_json(error.column),
      "message": @json.to_json(error.message),
    },
  }
  result.stringify()
}

///| The interactive boundary is smaller than the standalone parser limit.
fn parse_for_report(text : String, ports : Int) -> Result[Network, Diagnostic] {
  if text.length() > 2097152 {
    return Err(diagnostic(InputLimit, 1, 1, "Interactive input exceeds 2 Mi UTF-16 code units"))
  }
  parse_touchstone(text, ports, max_samples=20000)
}

///| Stable JSON boundary shared by the browser and Node CLI. No host parser.
/// Values are explicitly labeled so consumers need not depend on wire order.
/// This interface has a 2 Mi code-unit / 20000 sample budget.
pub fn analyze_touchstone_json(text : String, ports : Int) -> String {
  let network = match parse_for_report(text, ports) {
    Ok(value) => value
    Err(error) => return report_error(error)
  }
  let samples : Array[Json] = []
  for sample in network.samples {
    let values : Array[Json] = []
    for input = 1; input <= network.ports; input = input + 1 {
      for output = 1; output <= network.ports; output = output + 1 {
        let value = sample.values[(input - 1) * network.ports + output - 1]
        let item : Json = {
          "parameter": @json.to_json("S\{output}\{input}"),
          "output_port": @json.to_json(output),
          "input_port": @json.to_json(input),
          "re": @json.to_json(value.re),
          "im": @json.to_json(value.im),
          "magnitude": report_number(Some(value.magnitude())),
          "db": report_number(value.magnitude_db()),
          "phase_degrees": report_number(value.phase_degrees()),
        }
        values.push(item)
      }
    }
    let row : Json = {
      "frequency_hz": @json.to_json(sample.frequency_hz),
      "values": @json.to_json(values),
    }
    samples.push(row)
  }
  let result : Json = {
    "schema_version": @json.to_json(1),
    "ok": @json.to_json(true),
    "ports": @json.to_json(network.ports),
    "reference_ohms": @json.to_json(network.reference_ohms),
    "source_unit": @json.to_json(@debug.to_string(network.source_unit)),
    "source_format": @json.to_json(@debug.to_string(network.source_format)),
    "sample_count": @json.to_json(network.samples.length()),
    "samples": @json.to_json(samples),
  }
  result.stringify()
}

///| Export normalized CSV through the same checked boundary and limits.
pub fn export_touchstone_csv_json(text : String, ports : Int) -> String {
  match parse_for_report(text, ports) {
    Err(error) => report_error(error)
    Ok(network) => {
      let result : Json = {
        "schema_version": @json.to_json(1),
        "ok": @json.to_json(true),
        "csv": @json.to_json(network.to_csv()),
      }
      result.stringify()
    }
  }
}
