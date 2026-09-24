// SPDX-License-Identifier: Apache-2.0

///|
test "source slices use scalar positions after a surrogate pair" {
  let slices = make_slices("甲😀\r\n-1")
  @test.assert_eq(slices.fragment(4, 6), "-1")
}

///|
test "a non-BMP character occupies one parser position" {
  let slices = make_slices("a😀b")
  @test.assert_eq(slices.fragment(1, 2), "😀")
  @test.assert_eq(slices.fragment(2, 3), "b")
}

///|
test "source slices preserve original CRLF and tabs" {
  let slices = make_slices("中\r\n\t1")
  @test.assert_eq(slices.fragment(1, 4), "\r\n\t")
  @test.assert_eq(slices.fragment(4, 5), "1")
}

///|
test "empty and ASCII source slices" {
  @test.assert_eq(make_slices("").fragment(0, 0), "")
  @test.assert_eq(make_slices("(-1 : Int)").fragment(1, 3), "-1")
}
