///|
/// Split a comment label without applying data-token limits to ordinary prose.
fn metadata_word(text : StringView) -> (StringView, StringView) {
  let rest = text.trim_start(chars=" \t")
  match rest.find_by(ch => ch == ' ' || ch == '\t') {
    Some(index) => rest.split_at(index)
    None => (rest, "")
  }
}

///|
/// A narrow safety guard, not a general HFSS/Touchstone metadata parser.
/// Recognized Port Impedance declarations must be single-line, common-real and
/// exactly equal to header R. Never renormalize S values or guess missing fields.
fn check_impedance_comment(
  line : String,
  line_number : Int,
  ports : Int,
  options : Options?,
) -> Result[Unit, Diagnostic] {
  let (before, comment) = match line.split_once("!") {
    Some(pair) => pair
    None => return Ok(())
  }
  let (first, rest) = metadata_word(comment)
  if first.length() != 4 || !first.to_owned().equal_ignore_ascii_case("Port") {
    return Ok(())
  }
  let (second, _) = metadata_word(rest)
  if second.length() != 9 ||
    !second.to_owned().equal_ignore_ascii_case("Impedance") {
    return Ok(())
  }
  let offset = before.char_length() + 1
  // Only standalone declarations after the option line are covered. Refuse
  // ambiguous inline forms instead of silently treating them as harmless prose.
  if !before.trim(chars=" \t\uFEFF").is_empty() {
    return Err(
      diagnostic(
        UnsupportedMetadata,
        line_number,
        offset,
        "Port Impedance metadata must be a standalone comment after the option line",
      ),
    )
  }
  let reference = match options {
    Some(value) => value.reference
    None =>
      return Err(
        diagnostic(
          UnsupportedMetadata,
          line_number,
          offset,
          "Port Impedance metadata before the option line is unsupported",
        ),
      )
  }
  // Line zero disables the initial-file BOM exception in the data lexer.
  let tokens = match tokenize_line(comment.to_owned(), 0) {
    Ok(value) => value
    Err(error) =>
      return Err(
        diagnostic(
          UnsupportedMetadata,
          line_number,
          offset + error.column,
          "Malformed or oversized Port Impedance metadata",
        ),
      )
  }
  if tokens.length() != 2 + 2 * ports {
    return Err(
      diagnostic(
        UnsupportedMetadata,
        line_number,
        offset,
        "Expected exactly one real/imaginary impedance pair per port on the same comment line",
      ),
    )
  }
  for port = 0; port < ports; port = port + 1 {
    for part = 0; part < 2; part = part + 1 {
      let source = tokens[2 + 2 * port + part]
      let token : Token = {
        text: source.text,
        line: line_number,
        column: offset + source.column,
      }
      let value = match number(token) {
        Ok(value) => value
        Err(_) =>
          return Err(
            diagnostic(
              UnsupportedMetadata,
              token.line,
              token.column,
              "Port Impedance metadata contains an invalid or unrepresentable number",
            ),
          )
      }
      let expected = if part == 0 { reference } else { 0.0 }
      if value != expected {
        return Err(
          diagnostic(
            UnsupportedMetadata,
            token.line,
            token.column,
            "Port Impedance metadata conflicts with common real header R; re-export with a common real reference impedance",
          ),
        )
      }
    }
  }
  Ok(())
}
