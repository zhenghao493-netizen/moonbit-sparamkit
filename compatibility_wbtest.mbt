///|
test "CR-only line endings parse both port counts" {
  let one = parse_touchstone("! legacy\r# Hz S RI R 50\r1 .3 -.4\r2 .2 .1\r", 1).unwrap()
  assert_true(one.samples.length() == 2)
  assert_near(one.get_s(0, 1, 1).unwrap().im, -0.4)
  let two = parse_touchstone("# Hz S RI R 50\r1 .1 0 .2 0\r.3 0 .4 0\r", 2).unwrap()
  assert_near(two.get_s(0, 1, 2).unwrap().re, 0.3)
}

///|
test "mixed line endings keep diagnostic physical location" {
  let error = parse_touchstone("! a\r\n# Hz S RI R 50\r1 0 0\n2 bad 0", 1).unwrap_err()
  assert_true(error.code == InvalidNumber)
  assert_true(error.line == 4 && error.column == 3)
}

///|
test "single initial BOM accepted" {
  let net = parse_touchstone("\uFEFF# Hz S RI R 50\n1 .5 0", 1).unwrap()
  assert_near(net.get_s(0, 1, 1).unwrap().re, 0.5)
}

///|
test "BOM before first comment with CRLF accepted" {
  let net = parse_touchstone("\uFEFF! exported file\r\n# Hz S RI R 50\r\n1 0 1", 1).unwrap()
  assert_near(net.get_s(0, 1, 1).unwrap().im, 1.0)
}

///|
test "BOM is not ignored in a numeric token" {
  expect_error("# Hz S RI R 50\n1 \uFEFF.5 0", 1, InvalidNumber)
}

///|
test "BOM on subsequent line is not an encoding marker" {
  expect_error("# Hz S RI R 50\n\uFEFF1 0 0", 1, InvalidNumber)
}

///|
test "duplicate BOM does not get repeatedly stripped" {
  expect_error("\uFEFF\uFEFF# Hz S RI R 50\n1 0 0", 1, MissingOptions)
}

///|
test "initial BOM counts in first-line source column" {
  let error = parse_touchstone("\uFEFF# bad\n1 0 0", 1).unwrap_err()
  assert_true(error.line == 1 && error.column == 4)
}

///|
test "all option category permutations give same network" {
  let options = ["MHz", "S", "RI", "R 75"]
  for a = 0; a < 4; a = a + 1 {
    for b = 0; b < 4; b = b + 1 {
      for c = 0; c < 4; c = c + 1 {
        for d = 0; d < 4; d = d + 1 {
          if a == b || a == c || a == d || b == c || b == d || c == d { continue }
          let text = "# \{options[a]} \{options[b]} \{options[c]} \{options[d]}\n1 .3 -.4"
          let net = parse_touchstone(text, 1).unwrap()
          assert_near(net.reference_ohms, 75.0)
          assert_near(net.samples[0].frequency_hz, 1000000.0)
          assert_near(net.get_s(0, 1, 1).unwrap().re, 0.3)
        }
      }
    }
  }
}

///|
test "every two-port continuation split preserves wire order" {
  let fields = ["1", ".1", ".11", ".2", ".22", ".3", ".33", ".4", ".44"]
  for split = 1; split < fields.length(); split = split + 1 {
    let mut text = "# Hz S RI R 50\n"
    for i = 0; i < fields.length(); i = i + 1 {
      text = text + (if i == split { "\n! continuation\n" } else { " " }) + fields[i]
    }
    let net = parse_touchstone(text, 2).unwrap()
    assert_near(net.get_s(0, 2, 1).unwrap().im, 0.22)
    assert_near(net.get_s(0, 1, 2).unwrap().im, 0.33)
  }
}

///|
test "comment-only input remains no data with every line ending" {
  for newline in ["\n", "\r\n", "\r"] {
    expect_error("! one" + newline + "! two", 1, NoData)
  }
}

///|
test "duplicate options rejected even with CR-only input" {
  expect_error("#\r1 .1 0\r# Hz S RI R 50", 1, DuplicateOptions)
}

///|
test "non-ASCII numeric whitespace is not silently accepted" {
  expect_error("# Hz S RI R 50\n1\u00A0.5 0", 1, IncompleteRecord)
}

///|
test "signed zero and zero with exponent are legitimate zero" {
  let net = parse_touchstone("# Hz S RI R 50\n-0 -0.0 +0e12\n1 0 0", 1).unwrap()
  assert_near(net.samples[0].frequency_hz, 0.0)
  assert_true(net.get_s(0, 1, 1).unwrap().magnitude_db() is None)
}

///|
test "comments cannot hide an extra numeric field" {
  expect_error("# Hz S RI R 50\n1 .5 0 99 ! note", 1, ExtraFields)
}

///|
test "CR-only incomplete record position retained" {
  let error = parse_touchstone("! note\r# Hz S RI R 50\r1 .5", 1).unwrap_err()
  assert_true(error.code == IncompleteRecord)
  assert_true(error.line == 3 && error.column == 1)
}

///|
test "JSON bridge accepts the same BOM and CR variant as library" {
  let result = analyze_touchstone_json("\uFEFF# Hz S RI R 50\r1 .3 -.4\r", 1)
  assert_true(result.contains("\"ok\":true"))
  assert_true(result.contains("\"sample_count\":1"))
}

///|
test "bounded sample count still enforced with CR-only input" {
  let error = parse_touchstone("# Hz S RI R 50\r1 0 0\r2 0 0", 1, max_samples=1).unwrap_err()
  assert_true(error.code == SampleLimit && error.line == 3)
}
