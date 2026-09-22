///|
fn report_field(text : String, key : String) -> Json raise {
  let parsed = @json.parse(text)
  guard parsed is Object(fields) else { fail("Expected report object") }
  guard fields.get(key) is Some(value) else { fail("Missing report key") }
  value
}

///|
test "report success has explicit schema and sample count" {
  let text = analyze_touchstone_json("# Hz S RI R 75\n1 0.3 -0.4", 1)
  @debug.assert_eq(report_field(text, "schema_version"), @json.to_json(1))
  @debug.assert_eq(report_field(text, "sample_count"), @json.to_json(1))
  @debug.assert_eq(report_field(text, "reference_ohms"), @json.to_json(75.0))
  @debug.assert_eq(report_field(text, "ok"), @json.to_json(true))
}

///|
test "report labels asymmetric two-port data" {
  let text = analyze_touchstone_json("# Hz S RI R 50\n1 .1 0 .2 0 .3 0 .4 0", 2)
  assert_true(text.contains("S11"))
  assert_true(text.contains("S21"))
  assert_true(text.contains("S12"))
  assert_true(text.contains("S22"))
}

///|
test "zero phase and dB produce valid JSON null" {
  let text = analyze_touchstone_json("# Hz S RI R 50\n1 0 0", 1)
  assert_true(@json.valid(text))
  assert_true(text.contains("null"))
  assert_false(text.contains("NaN"))
  assert_false(text.contains("Infinity"))
}

///|
test "report preserves parser failure and line location" {
  let text = analyze_touchstone_json("# Hz S RI R 50\n1 bad 0", 1)
  @debug.assert_eq(report_field(text, "ok"), @json.to_json(false))
  guard report_field(text, "error") is Object(fields) else { fail("Missing error") }
  @debug.assert_eq(fields.get("line"), Some(@json.to_json(2)))
  @debug.assert_eq(fields.get("code"), Some(@json.to_json("InvalidNumber")))
}

///|
test "report validates ports" {
  let text = analyze_touchstone_json("#\n1 1 0", 3)
  @debug.assert_eq(report_field(text, "ok"), @json.to_json(false))
}

///|
test "CSV report uses core CSV encoder" {
  let source = "# Hz S RI R 50\n1 0.5 0"
  let expected = parse_touchstone(source, 1).unwrap().to_csv()
  @debug.assert_eq(report_field(export_touchstone_csv_json(source, 1), "csv"), @json.to_json(expected))
}

///|
test "CSV report rejects malformed input" {
  @debug.assert_eq(report_field(export_touchstone_csv_json("# Hz S RI\n1 0", 1), "ok"), @json.to_json(false))
}

///|
test "report does not serialize overflowed derived magnitude" {
  let text = analyze_touchstone_json("# Hz S RI R 50\n1 1.7e308 1.7e308", 1)
  @debug.assert_eq(report_field(text, "ok"), @json.to_json(true))
  assert_true(@json.valid(text))
  assert_false(text.contains("Infinity"))
}
