///|
/// These tests compile against the public package, not its private helpers.
fn api_near(actual : Double, expected : Double) -> Unit raise {
  assert_true((actual - expected).abs() <= 1.0e-11 * (1.0 + expected.abs()))
}

///|
test "public API: README two-port usage" {
  let text = "# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n"
  let network = @sparamkit.parse_touchstone(text, 2).unwrap()
  let s21 = network.get_s(0, 2, 1).unwrap()
  api_near(s21.re, 0.8)
  api_near(s21.im, -0.1)
  assert_true(network.to_csv().contains("1000000000,50,2,1,0.8,-0.1"))
}

///|
test "public API: source enums and sample fields are accessible" {
  let network = @sparamkit.parse_touchstone("# MHz S MA R 75\n2 .5 90", 1).unwrap()
  assert_true(network.source_format == @sparamkit.MA)
  assert_true(network.source_unit == @sparamkit.MHz)
  assert_eq(network.ports, 1)
  api_near(network.reference_ohms, 75.0)
  api_near(network.samples[0].frequency_hz, 2000000.0)
  api_near(network.samples[0].values[0].im, 0.5)
}

///|
test "public API: invalid indices return None" {
  let network = @sparamkit.parse_touchstone("# Hz S RI R 50\n1 .3 -.4", 1).unwrap()
  for
    (sample, output, input) in [
      (-1, 1, 1),
      (1, 1, 1),
      (0, 0, 1),
      (0, 2, 1),
      (0, 1, 0),
      (0, 1, 2),
    ] {
    guard network.get_s(sample, output, input) is None else {
      fail("Out-of-range indices must not return a value")
    }
  }
}

///|
test "public API: caller can set a sample budget" {
  let result = @sparamkit.parse_touchstone(
    "# Hz S RI R 50\n1 .1 0\n2 .2 0",
    1,
    max_samples=1,
  )
  guard result is Err(error) else { fail("Expected sample budget error") }
  assert_true(error.code == @sparamkit.SampleLimit)
  assert_eq(error.line, 3)
}

///|
test "public API: diagnostic fields and code are accessible" {
  let result = @sparamkit.parse_touchstone("# Hz S RI R 50\n1 bad 0", 1)
  guard result is Err(error) else { fail("Expected invalid number") }
  assert_true(error.code == @sparamkit.InvalidNumber)
  assert_eq(error.line, 2)
  assert_eq(error.column, 3)
  assert_true(error.message.contains("bad"))
}

///|
test "public API: consumer constructs a complex value" {
  let value : @sparamkit.Complex = { re: 0.3, im: -0.4, }
  api_near(value.magnitude(), 0.5)
  api_near(value.magnitude_db().unwrap(), -6.020599913279624)
  api_near(value.phase_degrees().unwrap(), -53.13010235415598)
}

///|
test "public API: zero metrics remain optional" {
  let value : @sparamkit.Complex = { re: 0.0, im: 0.0, }
  assert_eq(value.magnitude(), 0.0)
  guard value.magnitude_db() is None else { fail("Zero dB is undefined") }
  guard value.phase_degrees() is None else { fail("Zero phase is undefined") }
}

///|
test "public API: JSON report can be consumed without internal types" {
  let text = @sparamkit.analyze_touchstone_json("# Hz S RI R 50\n1 0 0", 1)
  guard @json.parse(text) is Object(fields) else { fail("Expected object") }
  @debug.assert_eq(fields.get("schema_version"), Some(@json.to_json(1)))
  @debug.assert_eq(fields.get("sample_count"), Some(@json.to_json(1)))
  @debug.assert_eq(fields.get("ok"), Some(@json.to_json(true)))
  assert_true(text.contains("\"db\":null"))
  assert_true(text.contains("\"phase_degrees\":null"))
}

///|
test "public API: CSV envelope matches library export" {
  let source = "# Hz S RI R 75\n1 .3 -.4\n2 .2 -.1"
  let expected = @sparamkit.parse_touchstone(source, 1).unwrap().to_csv()
  guard @json.parse(@sparamkit.export_touchstone_csv_json(source, 1))
    is Object(fields) else {
    fail("Expected object")
  }
  @debug.assert_eq(fields.get("csv"), Some(@json.to_json(expected)))
}

///|
test "public API: metadata conflict is a structured error" {
  let source = "# Hz S RI R 50\n1 .1 0\n! Port Impedance 75 0"
  guard @sparamkit.parse_touchstone(source, 1) is Err(error) else {
    fail("Expected conflict")
  }
  assert_true(error.code == @sparamkit.UnsupportedMetadata)
  assert_eq(error.line, 3)
  let csv = @sparamkit.export_touchstone_csv_json(source, 1)
  guard @json.parse(csv) is Object(fields) else { fail("Expected object") }
  @debug.assert_eq(fields.get("ok"), Some(@json.to_json(false)))
  assert_true(fields.get("csv") is None)
}
