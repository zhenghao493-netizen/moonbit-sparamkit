// SPDX-License-Identifier: Apache-2.0

///|
struct GroupedConstraintFragments {
  source : String
  fragments : Array[String]
}

///|
extend GroupedConstraintFragments with @syntax.IterVisitor::{base, visit_Impl}

///|
impl @syntax.IterVisitor for GroupedConstraintFragments with fn visit_Pattern_Constraint(
  self,
  pat~,
  ty~,
  loc~,
) {
  self.fragments.push(self.source[loc.start.cnum:loc.end.cnum].to_owned())
  @syntax.IterVisitor::visit_Pattern_Constraint(self.base(), pat~, ty~, loc~)
}

///|
fn grouped_constraint_ast(
  source : String,
  impls : @syntax.Impls,
  expected : Array[String],
) -> Json raise Error {
  let visitor : GroupedConstraintFragments = { source, fragments: [], }
  for impl_ in impls {
    visitor.visit_Impl(impl_)
  }
  @test.assert_eq(visitor.fragments, expected)
  @basic.show_loc.protect(String, fn() {
    ToJson::to_json(impls.map(impl_ => impl_.json_repr()))
  })
}

///|
fn assert_grouped_constraint_locations(
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
  let hand_json = grouped_constraint_ast(source, hand, expected)
  let yacc_json = grouped_constraint_ast(source, yacc, expected)
  let cst_json = grouped_constraint_ast(source, lowered, expected)
  @test.assert_eq(hand_json, yacc_json)
  @test.assert_eq(hand_json, cst_json)
}

///|
test "direct constraint includes its own parentheses" {
  assert_grouped_constraint_locations("fn f(x) { let (x : Int) = x; x }", [
    "(x : Int)",
  ])
}

///|
test "grouped constraint ignores an extra pair of parentheses" {
  assert_grouped_constraint_locations("fn f(x) { let ((x : Int)) = x; x }", [
    "(x : Int)",
  ])
}

///|
test "triply grouped constraint preserves the original span" {
  assert_grouped_constraint_locations(
    "fn f(x) { match x { (((x : Int))) => 1; _ => 0 } }",
    ["(x : Int)"],
  )
}

///|
test "grouping an annotated tuple preserves the constraint span" {
  assert_grouped_constraint_locations(
    "fn f(x) { let (((a, b) : (Int, Int))) = x; a }",
    ["((a, b) : (Int, Int))"],
  )
}

///|
test "grouped constraint inside a constructor preserves its span" {
  assert_grouped_constraint_locations(
    "fn f(x) { match x { Some(((x : Int))) => x; _ => 0 } }",
    ["(x : Int)"],
  )
}

///|
test "grouped constraint inside an array preserves its span" {
  assert_grouped_constraint_locations(
    "fn f(x) { match x { [((x : Int))] => x; _ => 0 } }",
    ["(x : Int)"],
  )
}

///|
test "nested annotations retain each annotation's own parentheses" {
  assert_grouped_constraint_locations(
    "fn f(x) { let (((x : Int) : Int)) = x; x }",
    ["((x : Int) : Int)", "(x : Int)"],
  )
}

///|
test "multiline grouping leaves the inner constraint span unchanged" {
  assert_grouped_constraint_locations(
    "fn f(x) { match x { (\n(x : Int)\n) => x; _ => 0 } }",
    ["(x : Int)"],
  )
}

///|
test "ordinary tuple locations remain unchanged" {
  assert_grouped_constraint_locations("fn f(x) { let ((a, b)) = x; a }", [])
}

///|
test "ordinary grouped variable locations remain unchanged" {
  assert_grouped_constraint_locations("fn f(x) { let (((y))) = x; y }", [])
}
