///|
/// Ignore comments before token construction; bound tokens before allocating more.
fn tokenize_line(
  line : String,
  line_number : Int,
) -> Result[Array[Token], Diagnostic] {
  let tokens : Array[Token] = []
  let mut word = ""
  let mut start_column = 1
  let mut column = 0
  for ch in line.iter() {
    // Accept a BOM only at the very beginning; source columns still count it.
    if line_number == 1 && column == 0 && ch == '\uFEFF' {
      column = column + 1
      continue
    }
    column = column + 1
    if ch == '!' {
      break
    }
    if ch == ' ' || ch == '\t' || ch == '\r' {
      if word != "" {
        tokens.push({ text: word, line: line_number, column: start_column, })
        word = ""
      }
    } else if ch == '#' && tokens.length() == 0 && word == "" {
      tokens.push({ text: "#", line: line_number, column, })
    } else {
      if word == "" {
        // A supported option/data line needs at most 9 tokens. Bound the lexer
        // itself so malformed, short-token input cannot allocate millions of
        // Token values before the record-width check is reached.
        if tokens.length() >= 16 {
          return Err(
            diagnostic(
              LineTokenLimit,
              line_number,
              column,
              "Line exceeds 16 tokens",
            ),
          )
        }
        start_column = column
      }
      let piece = ch.to_string()
      if word.length() + piece.length() > 128 {
        return Err(
          diagnostic(
            TokenLimit,
            line_number,
            start_column,
            "Token exceeds 128 code units",
          ),
        )
      }
      word = word + piece
    }
  }
  if word != "" {
    tokens.push({ text: word, line: line_number, column: start_column, })
  }
  Ok(tokens)
}

///|
/// Decimal grammar only: optional sign, decimal digits/dot, optional E exponent.
/// The standard library handles binary64 conversion; this layer excludes NaN,
/// infinity, hexadecimal numbers, underscores and partially valid tokens.
fn decimal_syntax(text : String) -> Bool {
  let chars = text.to_array()
  let n = chars.length()
  let mut i = 0
  if i < n && (chars[i] == '+' || chars[i] == '-') {
    i = i + 1
  }
  let mut digits = 0
  while i < n && chars[i] >= '0' && chars[i] <= '9' {
    digits = digits + 1
    i = i + 1
  }
  if i < n && chars[i] == '.' {
    i = i + 1
    while i < n && chars[i] >= '0' && chars[i] <= '9' {
      digits = digits + 1
      i = i + 1
    }
  }
  if digits == 0 {
    return false
  }
  if i < n && (chars[i] == 'e' || chars[i] == 'E') {
    i = i + 1
    if i < n && (chars[i] == '+' || chars[i] == '-') {
      i = i + 1
    }
    let exponent_start = i
    while i < n && chars[i] >= '0' && chars[i] <= '9' {
      i = i + 1
    }
    if i == exponent_start {
      return false
    }
  }
  i == n
}

///|
fn number(token : Token) -> Result[Double, Diagnostic] {
  if !decimal_syntax(token.text) {
    return Err(
      diagnostic(
        InvalidNumber,
        token.line,
        token.column,
        "Expected a decimal number, got '\{token.text}'",
      ),
    )
  }
  let value = @string.parse_double(token.text.view()) catch {
    _ =>
      return Err(
        diagnostic(
          NumericRange,
          token.line,
          token.column,
          "Decimal cannot be converted to Double",
        ),
      )
  }
  if !finite(value) {
    return Err(
      diagnostic(
        NumericRange,
        token.line,
        token.column,
        "Non-finite or overflowing number",
      ),
    )
  }
  if value == 0.0 {
    for ch in token.text.iter() {
      if ch == 'e' || ch == 'E' {
        break
      }
      if ch >= '1' && ch <= '9' {
        return Err(
          diagnostic(
            NumericRange,
            token.line,
            token.column,
            "Nonzero decimal underflows to zero",
          ),
        )
      }
    }
  }
  Ok(value)
}
