///|
fn assert_near(actual : Double, expected : Double) -> Unit raise {
  assert_true((actual - expected).abs() <= 1e-11 * (1.0 + expected.abs()))
}

///|
fn expect_error(text : String, ports : Int, code : ErrorCode) -> Unit raise {
  match parse_touchstone(text, ports) {
    Ok(_) => fail("Expected a structured error")
    Err(error) => assert_true(error.code == code)
  }
}

///|
test "one-port RI and metadata" {
  let net = parse_touchstone("# MHz S RI R 75\n100 0.3 -0.4\n", 1).unwrap()
  assert_true(net.ports == 1)
  assert_true(net.source_format == RI)
  assert_near(net.reference_ohms, 75.0)
  assert_near(net.samples[0].frequency_hz, 100000000.0)
  let value = net.get_s(0, 1, 1).unwrap()
  assert_near(value.re, 0.3)
  assert_near(value.im, -0.4)
  assert_near(value.magnitude(), 0.5)
}

///|
test "two-port wire order is S11 S21 S12 S22, not row-major" {
  let net = parse_touchstone("# Hz S RI R 50\n1 0.1 0.11 0.2 0.22 0.3 0.33 0.4 0.44", 2).unwrap()
  assert_near(net.get_s(0, 1, 1).unwrap().re, 0.1)
  assert_near(net.get_s(0, 2, 1).unwrap().re, 0.2)
  assert_near(net.get_s(0, 1, 2).unwrap().re, 0.3)
  assert_near(net.get_s(0, 2, 2).unwrap().im, 0.44)
}

///|
test "MA to complex" {
  let net = parse_touchstone("# GHz S MA R 50\n1 0.5 90", 1).unwrap()
  let s = net.get_s(0, 1, 1).unwrap()
  assert_near(s.re, 0.0)
  assert_near(s.im, 0.5)
  assert_near(s.phase_degrees().unwrap(), 90.0)
}

///|
test "DB to complex uses voltage ratio divisor twenty" {
  let net = parse_touchstone("# Hz S DB R 50\n1 -20 -90", 1).unwrap()
  let s = net.get_s(0, 1, 1).unwrap()
  assert_near(s.re, 0.0)
  assert_near(s.im, -0.1)
  assert_near(s.magnitude_db().unwrap(), -20.0)
}

///|
test "equivalent RI MA DB representations" {
  let ri = parse_touchstone("# Hz S RI R 50\n1 0 0.1", 1).unwrap().get_s(0, 1, 1).unwrap()
  let ma = parse_touchstone("# Hz S MA R 50\n1 0.1 90", 1).unwrap().get_s(0, 1, 1).unwrap()
  let db = parse_touchstone("# Hz S DB R 50\n1 -20 90", 1).unwrap().get_s(0, 1, 1).unwrap()
  assert_near(ri.re, ma.re)
  assert_near(ri.im, ma.im)
  assert_near(ri.re, db.re)
  assert_near(ri.im, db.im)
}

///|
test "option defaults are GHz S MA R50" {
  let net = parse_touchstone("#\n1 1 90", 1).unwrap()
  assert_near(net.samples[0].frequency_hz, 1e9)
  assert_near(net.reference_ohms, 50.0)
  assert_true(net.source_format == MA)
  assert_near(net.get_s(0, 1, 1).unwrap().im, 1.0)
}

///|
test "case-insensitive options and tight hash" {
  let net = parse_touchstone("#khz s ri r 50\n1 0.5 0", 1).unwrap()
  assert_near(net.samples[0].frequency_hz, 1000.0)
}

///|
test "each supported frequency unit" {
  let names = ["Hz", "kHz", "MHz", "GHz"]
  let scales = [1.0, 1000.0, 1000000.0, 1000000000.0]
  for i = 0; i < names.length(); i = i + 1 {
    let net = parse_touchstone("# \{names[i]} S RI R 50\n2 0 0", 1).unwrap()
    assert_near(net.samples[0].frequency_hz, 2.0 * scales[i])
  }
}

///|
test "comments tabs CRLF and trailing blank lines" {
  let net = parse_touchstone("! sample\r\n  # Hz S RI R 50 ! options\r\n\t1\t.5\t-0.25 ! sample\r\n\r\n", 1).unwrap()
  assert_true(net.samples.length() == 1)
  assert_near(net.get_s(0, 1, 1).unwrap().re, 0.5)
}

///|
test "record continuation with intervening comment" {
  let net = parse_touchstone("# Hz S RI R 50\n1 .1 0 .2 0\n! continued\n.3 0 .4 0", 2).unwrap()
  assert_near(net.get_s(0, 1, 2).unwrap().re, 0.3)
}

///|
test "scientific notation and explicit positive sign" {
  let net = parse_touchstone("# Hz S RI R 50\n+1.25E+3 -2.5e-1 +.75", 1).unwrap()
  assert_near(net.samples[0].frequency_hz, 1250.0)
  assert_near(net.get_s(0, 1, 1).unwrap().im, 0.75)
}

///|
test "optional header values and recognized order" {
  let net = parse_touchstone("# S RI R 75 MHz\n2 0 0", 1).unwrap()
  assert_near(net.reference_ohms, 75.0)
  assert_near(net.samples[0].frequency_hz, 2e6)
}

///|
test "zero frequency is supported" {
  let net = parse_touchstone("# Hz S RI R 50\n0 1 0\n1 0 1", 1).unwrap()
  assert_true(net.samples.length() == 2)
}

///|
test "invalid port count is not inferred" {
  expect_error("#\n1 0 0", 0, UnsupportedPorts)
  expect_error("#\n1 0 0", 3, UnsupportedPorts)
}

///|
test "missing option line" {
  expect_error("1 0 0", 1, MissingOptions)
}

///|
test "second option line is rejected" {
  expect_error("# Hz S RI R 50\n# MHz S RI R 50\n1 0 0", 1, DuplicateOptions)
}

///|
test "option change after data is rejected" {
  expect_error("# Hz S RI R 50\n1 0 0\n# MHz S RI R 50", 1, DuplicateOptions)
}

///|
test "unsupported parameter is not misread as S" {
  for kind in ["Y", "Z", "H", "G"] {
    expect_error("# Hz \{kind} RI R 50\n1 0 0", 1, UnsupportedParameter)
  }
}

///|
test "Touchstone2 keyword is explicitly rejected" {
  expect_error("[Version] 2.0\n# Hz S RI R 50", 1, UnsupportedVersion)
  expect_error("# Hz S RI R 50\n[Network Data]\n1 0 0", 1, UnsupportedVersion)
}

///|
test "unknown option" {
  expect_error("# THz S RI R 50\n1 0 0", 1, InvalidOption)
}

///|
test "duplicate option categories" {
  for header in ["# Hz GHz S RI", "# Hz S RI MA", "# Hz S S RI", "# Hz S RI R 50 R 75"] {
    expect_error(header + "\n1 0 0", 1, InvalidOption)
  }
}

///|
test "missing and invalid reference resistance" {
  expect_error("# Hz S RI R\n1 0 0", 1, InvalidReference)
  expect_error("# Hz S RI R 0\n1 0 0", 1, InvalidReference)
  expect_error("# Hz S RI R -50\n1 0 0", 1, InvalidReference)
}

///|
test "incomplete one-port record" {
  expect_error("# Hz S RI R 50\n1 0.1", 1, IncompleteRecord)
}

///|
test "incomplete two-port record" {
  expect_error("# Hz S RI R 50\n1 .1 0 .2 0 .3 0 .4", 2, IncompleteRecord)
}

///|
test "extra field is not silently ignored" {
  expect_error("# Hz S RI R 50\n1 0 0 9", 1, ExtraFields)
}

///|
test "empty input and header without samples" {
  expect_error("", 1, NoData)
  expect_error("# Hz S RI R 50\n! no data", 1, NoData)
}

///|
test "invalid decimal grammar" {
  for text in ["nan", "NaN", "inf", "Infinity", "0x10", "1_000", ".", "+", "1e", "1e+", "1.2.3", "1junk"] {
    expect_error("# Hz S RI R 50\n1 \{text} 0", 1, InvalidNumber)
  }
}

///|
test "number overflow and underflow" {
  expect_error("# Hz S RI R 50\n1 1e309 0", 1, NumericRange)
  expect_error("# Hz S RI R 50\n1 1e-999 0", 1, NumericRange)
}

///|
test "negative magnitude is invalid in MA" {
  expect_error("# Hz S MA R 50\n1 -0.1 0", 1, InvalidMagnitude)
}

///|
test "negative frequency rejected" {
  expect_error("# Hz S RI R 50\n-1 .5 0", 1, InvalidFrequency)
}

///|
test "decreasing and duplicate frequency rejected" {
  expect_error("# Hz S RI R 50\n2 0 0\n1 0 0", 1, FrequencyOrder)
  expect_error("# Hz S RI R 50\n1 0 0\n1 0 0", 1, FrequencyOrder)
}

///|
test "frequency unit multiplication overflow" {
  expect_error("# GHz S RI R 50\n1e308 0 0", 1, NumericRange)
}

///|
test "decibel conversion overflow and underflow" {
  expect_error("# Hz S DB R 50\n1 10000 0", 1, NumericRange)
  expect_error("# Hz S DB R 50\n1 -10000 0", 1, NumericRange)
}

///|
test "zero magnitude has undefined phase and finite dB absent" {
  let s = parse_touchstone("# Hz S RI R 50\n1 0 0", 1).unwrap().get_s(0, 1, 1).unwrap()
  assert_true(s.phase_degrees() is None)
  assert_true(s.magnitude_db() is None)
}

///|
test "large and negative angle normalization" {
  let first = parse_touchstone("# Hz S MA R 50\n1 .5 450", 1).unwrap().get_s(0, 1, 1).unwrap()
  let second = parse_touchstone("# Hz S MA R 50\n1 .5 -270", 1).unwrap().get_s(0, 1, 1).unwrap()
  assert_near(first.im, 0.5)
  assert_near(first.re, second.re)
  assert_near(first.im, second.im)
}

///|
test "diagnostic preserves source line and column" {
  let error = parse_touchstone("! comment\n# Hz S RI R 50\n1 abc 0", 1).unwrap_err()
  assert_true(error.code == InvalidNumber)
  assert_true(error.line == 3)
  assert_true(error.column == 3)
}

///|
test "sample resource limit" {
  let error = parse_touchstone("# Hz S RI R 50\n1 0 0\n2 0 0", 1, max_samples=1).unwrap_err()
  assert_true(error.code == SampleLimit)
  let error = parse_touchstone("#\n1 0 0", 1, max_samples=0).unwrap_err()
  assert_true(error.code == SampleLimit)
}

///|
test "token resource limit" {
  let giant = "1".repeat(129)
  expect_error("# Hz S RI R 50\n1 \{giant} 0", 1, TokenLimit)
}

///|
test "safe port and sample lookup" {
  let net = parse_touchstone("# Hz S RI R 50\n1 0 0", 1).unwrap()
  assert_true(net.get_s(-1, 1, 1) is None)
  assert_true(net.get_s(1, 1, 1) is None)
  assert_true(net.get_s(0, 0, 1) is None)
  assert_true(net.get_s(0, 2, 1) is None)
}

///|
test "CSV export contains units and reference impedance" {
  let net = parse_touchstone("# Hz S RI R 75\n1 .25 .5", 1).unwrap()
  let csv = net.to_csv()
  assert_true(csv.has_prefix("frequency_hz,reference_ohms,output_port,input_port,re,im\n"))
  assert_true(csv.contains("0.25"))
  assert_true(csv.contains("75"))
  assert_true(csv.has_suffix("\n"))
}
