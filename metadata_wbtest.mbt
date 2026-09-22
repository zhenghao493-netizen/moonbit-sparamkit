///|
test "reject impedance comment conflicting with header" {
  let text = "# Hz S RI R 50\n1 .1 0\n! Port Impedance 75 0\n"
  let error = parse_touchstone(text, 1).unwrap_err()
  assert_true(error.code == UnsupportedMetadata)
  assert_eq(error.line, 3)
  assert_eq(error.column, 18)
}

///|
test "accept redundant common real impedance without changing S" {
  let net = parse_touchstone(
    "# Hz S RI R 50\n1 .1 -.2\n! Port Impedance 50 0\n", 1,
  ).unwrap()
  assert_eq(net.reference_ohms, 50.0)
  assert_eq(net.get_s(0, 1, 1).unwrap().im, -0.2)
}

///|
test "reject imaginary impedance even with matching real part" {
  assert_true(
    parse_touchstone("# Hz S RI R 50\n1 .1 0\n! Port Impedance 50 .01\n", 1).unwrap_err().code ==
    UnsupportedMetadata,
  )
}

///|
test "check every port of two-port metadata" {
  let prefix = "# Hz S RI R 50\n1 .1 0 .2 0 .3 0 .4 0\n"
  assert_eq(
    parse_touchstone(prefix + "! Port Impedance 50 0 50 0\n", 2).unwrap().ports,
    2,
  )
  assert_true(
    parse_touchstone(prefix + "! Port Impedance 50 0 75 0\n", 2).unwrap_err().code ==
    UnsupportedMetadata,
  )
}

///|
test "metadata labels tolerate case and horizontal whitespace" {
  assert_eq(
    parse_touchstone(
      "# Hz S RI R 75\n1 0 0\n  !\tPoRT \t ImpEDance\t7.5e1\t-0.0\n", 1,
    ).unwrap().reference_ohms,
    75.0,
  )
}

///|
test "reject incomplete multiline and matrix metadata" {
  for
    suffix in [
      "! Port Impedance\n", "! Port Impedance 50\n! 0\n", "! Port Impedance 50 0 50 0\n",
    ] {
    assert_true(
      parse_touchstone("# Hz S RI R 50\n1 0 0\n" + suffix, 1).unwrap_err().code ==
      UnsupportedMetadata,
    )
  }
}

///|
test "reject malformed and nonfinite impedance declarations" {
  for value in ["NaN", "Inf", "0x32", "1e9999", "1e-9999", "50junk"] {
    assert_true(
      parse_touchstone(
        "# Hz S RI R 50\n1 0 0\n! Port Impedance " + value + " 0\n",
        1,
      ).unwrap_err().code ==
      UnsupportedMetadata,
    )
  }
}

///|
test "check later impedance declarations for frequency dependence" {
  assert_true(
    parse_touchstone(
      "# Hz S RI R 50\n1 0 0\n! Port Impedance 50 0\n2 0 0\n! Port Impedance 49 0\n",
      1,
    ).unwrap_err().code ==
    UnsupportedMetadata,
  )
}

///|
test "ordinary comments remain unrestricted prose" {
  let text = "! " +
    "x".repeat(200) +
    "\n! Port 1 = IN\n! Port Impedances are documentation only\n# Hz S RI R 50\n1 0 0\n"
  assert_eq(parse_touchstone(text, 1).unwrap().samples.length(), 1)
}

///|
test "reject metadata before options and inline declarations" {
  for
    text in [
      "! Port Impedance 50 0\n# Hz S RI R 50\n1 0 0\n", "# Hz S RI R 50 ! Port Impedance 50 0\n1 0 0\n",
      "# Hz S RI R 50\n1 0 0 ! Port Impedance 75 0\n",
    ] {
    assert_true(
      parse_touchstone(text, 1).unwrap_err().code == UnsupportedMetadata,
    )
  }
}

///|
test "metadata diagnostics retain CR and BOM line positions" {
  let text = "\uFEFF# Hz S RI R 50\r1 0 0\r  ! Port Impedance 75 0\r"
  let error = parse_touchstone(text, 1).unwrap_err()
  assert_eq(error.line, 3)
  assert_eq(error.column, 20)
}

///|
test "metadata check does not normalize near-equal impedances" {
  assert_true(
    parse_touchstone(
      "# Hz S RI R 50\n1 0 0\n! Port Impedance 50.0000000001 0\n", 1,
    ).unwrap_err().code ==
    UnsupportedMetadata,
  )
}

///|
test "metadata failures are shared by JSON and CSV interfaces" {
  let text = "# Hz S RI R 50\n1 0 0\n! Port Impedance 75 0\n"
  for
    output in [
      analyze_touchstone_json(text, 1),
      export_touchstone_csv_json(text, 1),
    ] {
    assert_true(output.contains("UnsupportedMetadata"))
    assert_false(output.contains("\"ok\":true"))
  }
}

///|
test "metadata lexer bounds still apply" {
  let text = "# Hz S RI R 50\n1 0 0\n! Port Impedance " +
    "5".repeat(129) +
    " 0\n"
  assert_true(
    parse_touchstone(text, 1).unwrap_err().code == UnsupportedMetadata,
  )
}
