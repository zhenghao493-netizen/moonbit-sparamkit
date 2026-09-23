// SPDX-License-Identifier: Apache-2.0

///|
struct PatternFragments {
  source : String
  fragments : Array[String]
}

///|
extend PatternFragments with @syntax.IterVisitor::{visit_Impl}

///|
impl @syntax.IterVisitor for PatternFragments with fn visit_Pattern_Constant(
  self,
  c~,
  loc~,
) {
  ignore(c)
  self.fragments.push(self.source[loc.start.cnum:loc.end.cnum].to_owned())
}

///|
fn checked_pattern_fragments(
  source : String,
  impls : @syntax.Impls,
  expected : Array[String],
) -> Json raise Error {
  let visitor : PatternFragments = { source, fragments: [] }
  for impl_ in impls {
    visitor.visit_Impl(impl_)
  }
  @test.assert_eq(visitor.fragments, expected)
  @basic.show_loc.protect(String, fn() {
    ToJson::to_json(impls.map(impl_ => impl_.json_repr()))
  })
}

///|
fn assert_pattern_locations(
  source : String,
  expected : Array[String],
) -> Unit raise Error {
  let (hand, hand_reports) = @parser.parse_string(source, parser=Handrolled)
  let (yacc, yacc_reports) = @parser.parse_string(source, parser=MoonYacc)
  let cst = @untyped_cst.parse_structure(source)
  let (lowered, lower_reports) = cst.to_impls()
  @test.assert_eq(hand_reports.length(), 0)
  @test.assert_eq(yacc_reports.length(), 0)
  @test.assert_eq(cst.diagnostics_view().length(), 0)
  @test.assert_eq(lower_reports.length(), 0)
  let hand_json = checked_pattern_fragments(source, hand, expected)
  let yacc_json = checked_pattern_fragments(source, yacc, expected)
  let cst_json = checked_pattern_fragments(source, lowered, expected)
  @test.assert_eq(hand_json, yacc_json)
  @test.assert_eq(hand_json, cst_json)
}

///|
test "negative integer patterns include the sign" {
  assert_pattern_locations(
    "fn f(x) { match x { (-1, -1L, -0x10) => 1; _ => 0 } }",
    ["-1", "-1L", "-0x10"],
  )
}

///|
test "negative floating patterns include the sign" {
  assert_pattern_locations(
    "fn f(x) { match x { (-1.5, -1.5F) => 1; _ => 0 } }",
    ["-1.5", "-1.5F"],
  )
}

///|
test "negative pattern spans retain intervening whitespace" {
  assert_pattern_locations(
    "fn f(x) { match x { -  1 => 1; _ => 0 } }",
    ["-  1"],
  )
}

///|
test "negative range endpoints retain their signs" {
  assert_pattern_locations(
    "fn f(x) { match x { -3..=-1 => 1; _ => 0 } }",
    ["-3", "-1"],
  )
}

///|
test "negative alternative patterns retain their signs" {
  assert_pattern_locations(
    "fn f(x) { match x { -1 | -2 => 1; _ => 0 } }",
    ["-1", "-2"],
  )
}

///|
test "negative patterns nested in a constructor retain the sign" {
  assert_pattern_locations(
    "fn f(x) { match x { Some(-1) => 1; _ => 0 } }",
    ["-1"],
  )
}

///|
test "positive pattern spans remain unchanged" {
  assert_pattern_locations(
    "fn f(x) { match x { (1, 1.5, 1.5F) => 1; _ => 0 } }",
    ["1", "1.5", "1.5F"],
  )
}
