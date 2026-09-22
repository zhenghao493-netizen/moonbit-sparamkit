///|
fn decode_pair(
  first : Token,
  second : Token,
  format : DataFormat,
) -> Result[Complex, Diagnostic] {
  let a = match number(first) {
    Ok(value) => value
    Err(error) => return Err(error)
  }
  let b = match number(second) {
    Ok(value) => value
    Err(error) => return Err(error)
  }
  if format == RI {
    return Ok({ re: a, im: b, })
  }
  if format == MA && a < 0.0 {
    return Err(
      diagnostic(
        InvalidMagnitude,
        first.line,
        first.column,
        "MA magnitude must be nonnegative",
      ),
    )
  }
  let amplitude = if format == DB { @math.pow(10.0, a / 20.0) } else { a }
  if !finite(amplitude) || (format == DB && amplitude == 0.0) {
    return Err(
      diagnostic(
        NumericRange,
        first.line,
        first.column,
        "Magnitude conversion overflows or underflows",
      ),
    )
  }
  // Reduce in degrees before multiplying: avoid overflow for large finite angles.
  let radians = b % 360.0 * (@math.PI / 180.0)
  let re = amplitude * @math.cos(radians)
  let im = amplitude * @math.sin(radians)
  if !finite(re) || !finite(im) {
    return Err(
      diagnostic(
        NumericRange,
        first.line,
        first.column,
        "Complex conversion is non-finite",
      ),
    )
  }
  Ok({ re, im, })
}

///|
fn decode_record(
  tokens : Array[Token],
  options : Options,
  ports : Int,
) -> Result[Sample, Diagnostic] {
  let token = tokens[0]
  let raw_frequency = match number(token) {
    Ok(value) => value
    Err(error) => return Err(error)
  }
  if raw_frequency < 0.0 {
    return Err(
      diagnostic(
        InvalidFrequency,
        token.line,
        token.column,
        "Frequency must be nonnegative",
      ),
    )
  }
  let frequency_hz = raw_frequency * options.unit.scale()
  if !finite(frequency_hz) {
    return Err(
      diagnostic(
        NumericRange,
        token.line,
        token.column,
        "Frequency overflows when converted to Hz",
      ),
    )
  }
  let values : Array[Complex] = []
  for i = 0; i < ports * ports; i = i + 1 {
    match decode_pair(tokens[1 + 2 * i], tokens[2 + 2 * i], options.format) {
      Ok(value) => values.push(value)
      Err(error) => return Err(error)
    }
  }
  Ok({ frequency_hz, values, })
}

///|
/// Parse a documented strict Touchstone 1.x S-parameter subset.
/// An explicit option line is required; omitted option values use standard defaults.
/// Each logical record starts on a new line; records may continue across lines.
/// Frequency must be strictly increasing. Noise data and version-2 keywords are
/// outside this API's scope. Limits are enforced before large result allocation.
pub fn parse_touchstone(
  text : String,
  ports : Int,
  max_samples? : Int = 100000,
) -> Result[Network, Diagnostic] {
  if ports != 1 && ports != 2 {
    return Err(
      diagnostic(
        UnsupportedPorts,
        1,
        1,
        "Only one-port and two-port S-parameter files are supported",
      ),
    )
  }
  if max_samples < 1 {
    return Err(diagnostic(SampleLimit, 1, 1, "max_samples must be positive"))
  }
  if text.length() > 8388608 {
    return Err(
      diagnostic(InputLimit, 1, 1, "Input exceeds 8 Mi UTF-16 code units"),
    )
  }
  let samples : Array[Sample] = []
  let pending : Array[Token] = []
  let mut options : Options? = None
  let mut line_number = 0
  let record_width = 1 + 2 * ports * ports
  // Preserve physical line numbers across LF, CRLF and legacy CR input.
  let normalized = text
    .replace_all(old="\r\n", new="\n")
    .replace_all(old="\r", new="\n")
  for line_view in normalized.split("\n") {
    line_number = line_number + 1
    let tokens = match tokenize_line(line_view.to_owned(), line_number) {
      Ok(value) => value
      Err(error) => return Err(error)
    }
    if tokens.length() == 0 {
      continue
    }
    let first = tokens[0]
    if first.text.has_prefix("[") {
      return Err(
        diagnostic(
          UnsupportedVersion,
          first.line,
          first.column,
          "Touchstone keyword sections (including version 2) are not supported",
        ),
      )
    }
    if first.text == "#" {
      match options {
        Some(_) =>
          return Err(
            diagnostic(
              DuplicateOptions,
              first.line,
              first.column,
              "Only one option line is supported",
            ),
          )
        None => ()
      }
      options = match parse_options(tokens) {
        Ok(value) => Some(value)
        Err(error) => return Err(error)
      }
      continue
    }
    let active = match options {
      Some(value) => value
      None =>
        return Err(
          diagnostic(
            MissingOptions,
            first.line,
            first.column,
            "Expected # option line before data",
          ),
        )
    }
    if samples.length() >= max_samples {
      return Err(
        diagnostic(
          SampleLimit,
          first.line,
          first.column,
          "Sample limit reached",
        ),
      )
    }
    if tokens.length() + pending.length() > record_width {
      let bad = tokens[record_width - pending.length()]
      return Err(
        diagnostic(
          ExtraFields,
          bad.line,
          bad.column,
          "Too many fields; each logical record must start on a new line",
        ),
      )
    }
    for token in tokens {
      pending.push(token)
    }
    if pending.length() == record_width {
      let sample = match decode_record(pending, active, ports) {
        Ok(value) => value
        Err(error) => return Err(error)
      }
      match samples.last() {
        Some(previous) =>
          if sample.frequency_hz <= previous.frequency_hz {
            return Err(
              diagnostic(
                FrequencyOrder,
                pending[0].line,
                pending[0].column,
                "Frequencies must increase strictly; noise blocks are unsupported",
              ),
            )
          }
        None => ()
      }
      samples.push(sample)
      pending.clear()
    }
  }
  if pending.length() != 0 {
    let token = pending[0]
    return Err(
      diagnostic(
        IncompleteRecord,
        token.line,
        token.column,
        "Incomplete record: expected \{record_width} fields, found \{pending.length()}",
      ),
    )
  }
  if samples.length() == 0 {
    return Err(diagnostic(NoData, 1, 1, "No complete network data records"))
  }
  let active = match options {
    Some(value) => value
    None =>
      return Err(diagnostic(MissingOptions, 1, 1, "Missing # option line"))
  }
  Ok({
    ports,
    reference_ohms: active.reference,
    source_unit: active.unit,
    source_format: active.format,
    samples,
  })
}
