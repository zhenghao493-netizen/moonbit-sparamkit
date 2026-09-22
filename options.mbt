///|
/// Defaults: GHz, S, MA, R 50. Repeated/unknown options are never silently ignored.
fn parse_options(tokens : Array[Token]) -> Result[Options, Diagnostic] {
  let mut unit = GHz
  let mut format = MA
  let mut reference = 50.0
  let mut saw_unit = false
  let mut saw_format = false
  let mut saw_parameter = false
  let mut saw_reference = false
  let mut i = 1
  while i < tokens.length() {
    let token = tokens[i]
    let word = token.text.to_upper()
    match word {
      "HZ" | "KHZ" | "MHZ" | "GHZ" => {
        if saw_unit {
          return Err(
            diagnostic(
              InvalidOption,
              token.line,
              token.column,
              "Repeated frequency unit",
            ),
          )
        }
        saw_unit = true
        unit = match word {
          "HZ" => Hz
          "KHZ" => KHz
          "MHZ" => MHz
          _ => GHz
        }
      }
      "RI" | "MA" | "DB" => {
        if saw_format {
          return Err(
            diagnostic(
              InvalidOption,
              token.line,
              token.column,
              "Repeated data format",
            ),
          )
        }
        saw_format = true
        format = match word {
          "RI" => RI
          "MA" => MA
          _ => DB
        }
      }
      "S" => {
        if saw_parameter {
          return Err(
            diagnostic(
              InvalidOption,
              token.line,
              token.column,
              "Repeated parameter type",
            ),
          )
        }
        saw_parameter = true
      }
      "Y" | "Z" | "G" | "H" =>
        return Err(
          diagnostic(
            UnsupportedParameter,
            token.line,
            token.column,
            "Only S parameters are supported",
          ),
        )
      "R" => {
        if saw_reference {
          return Err(
            diagnostic(
              InvalidOption,
              token.line,
              token.column,
              "Repeated reference impedance",
            ),
          )
        }
        saw_reference = true
        i = i + 1
        if i >= tokens.length() {
          return Err(
            diagnostic(
              InvalidReference,
              token.line,
              token.column,
              "R must be followed by a positive real impedance",
            ),
          )
        }
        let ref_token = tokens[i]
        reference = match number(ref_token) {
          Ok(value) => value
          Err(error) => return Err(error)
        }
        if reference <= 0.0 {
          return Err(
            diagnostic(
              InvalidReference,
              ref_token.line,
              ref_token.column,
              "Reference impedance must be positive",
            ),
          )
        }
      }
      _ =>
        return Err(
          diagnostic(
            InvalidOption,
            token.line,
            token.column,
            "Unknown option '\{token.text}'",
          ),
        )
    }
    i = i + 1
  }
  Ok({ unit, format, reference, })
}
