///|
test "lexer stops before allocating seventeenth token" {
  let error = tokenize_line("0 ".repeat(17), 7).unwrap_err()
  assert_true(error.code == LineTokenLimit)
  assert_true(error.line == 7)
  assert_true(error.column == 33)
}

///|
test "lexer permits exactly sixteen tokens" {
  let tokens = tokenize_line("0 ".repeat(16), 1).unwrap()
  assert_true(tokens.length() == 16)
}

///|
test "comment content does not consume token budget" {
  let tokens = tokenize_line("1 .5 0 ! " + "ignored ".repeat(300), 1).unwrap()
  assert_true(tokens.length() == 3)
}

///|
test "lexer allows exactly 128 UTF16 units" {
  let tokens = tokenize_line("1".repeat(128), 1).unwrap()
  assert_true(tokens.length() == 1)
  assert_true(tokens[0].text.length() == 128)
}

///|
test "supplementary Unicode character cannot exceed token unit limit" {
  let error = tokenize_line("a".repeat(127) + "𝒙", 1).unwrap_err()
  assert_true(error.code == TokenLimit)
}

///|
test "many short fields report a bounded source diagnostic" {
  let error = parse_touchstone("# Hz S RI R 50\n" + "0 ".repeat(2000), 2).unwrap_err()
  assert_true(error.code == LineTokenLimit)
  assert_true(error.line == 2)
  assert_true(error.column == 33)
}
