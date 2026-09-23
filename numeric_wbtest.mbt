///|
fn assert_db_near(value : Complex, expected : Double) -> Unit raise {
  let actual = value.magnitude_db().unwrap()
  assert_true(finite(actual) && (actual - expected).abs() < 1.0e-10)
}

///|
test "dB stays finite when linear magnitude overflows" {
  let value : Complex = { re: 1.7e308, im: 1.7e308, }
  assert_true(value.magnitude().is_inf())
  assert_db_near(value, 6167.619278384205)
}

///|
test "equal minimum subnormal components keep the power of both components" {
  let value = parse_touchstone("# Hz S RI R 50\n1 5e-324 5e-324", 1)
    .unwrap()
    .get_s(0, 1, 1)
    .unwrap()
  assert_db_near(value, -6463.114006905676)
}

///|
test "unequal subnormal components avoid a rounded intermediate magnitude" {
  let value = parse_touchstone("# Hz S RI R 50\n1 1e-323 5e-324", 1)
    .unwrap()
    .get_s(0, 1, 1)
    .unwrap()
  assert_db_near(value, -6459.134606818956)
}

///|
test "small finite components preserve dB and phase" {
  let value : Complex = { re: 1.0e-320, im: 1.0e-320, }
  assert_db_near(value, -6396.989796742321)
  assert_near(value.phase_degrees().unwrap(), 45.0)
}

///|
test "dB is invariant under sign changes and component exchange" {
  for
    value in [
      Complex::{ re: 0.3, im: -0.4, },
      Complex::{ re: -0.4, im: 0.3, },
      Complex::{ re: -0.3, im: -0.4, },
      Complex::{ re: 0.4, im: 0.3, },
    ] {
    assert_db_near(value, -6.020599913279623)
  }
  assert_db_near({ re: 3.0e199, im: -4.0e199, }, 3993.97940008672)
}

///|
test "small orthogonal component remains visible in dB near unity" {
  let value : Complex = { re: 1.0, im: 1.0e-8, }
  let actual = value.magnitude_db().unwrap()
  assert_true((actual - 4.342944819032518e-16).abs() < 1.0e-28)
}

///|
test "zero and nonfinite caller values have no finite dB" {
  let zero : Complex = { re: 0.0, im: -0.0, }
  let invalid : Complex = { re: @math.ln(-1.0), im: 1.0, }
  let overflow : Complex = { re: @math.exp(1000.0), im: 1.0, }
  assert_true(zero.magnitude_db() is None)
  assert_true(invalid.magnitude_db() is None)
  assert_true(overflow.magnitude_db() is None)
  assert_db_near({ re: 0.0, im: -1.0, }, 0.0)
}

///|
test "JSON exposes finite dB separately from unrepresentable magnitude" {
  let source = "# Hz S RI R 50\n1 1.7e308 1.7e308\n2 0 0"
  let report = analyze_touchstone_json(source, 1)
  guard report_field(report, "samples") is Array(samples) else {
    fail("Expected samples")
  }
  guard samples[0] is Object(sample) else { fail("Expected sample") }
  guard sample.get("values") is Some(Array(values)) else {
    fail("Expected values")
  }
  guard values[0] is Object(fields) else { fail("Expected parameter") }
  assert_true(fields.get("magnitude") is Some(Null))
  guard fields.get("db") is Some(Number(db, ..)) else {
    fail("Expected finite dB")
  }
  assert_true((db - 6167.619278384205).abs() < 1.0e-10)
  assert_false(report.contains("Infinity"))
  assert_false(report.contains("NaN"))
  let csv = parse_touchstone(source, 1).unwrap().to_csv()
  assert_true(csv.contains("1.7e+308") || csv.contains("1.7e308"))
}
