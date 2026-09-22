///|
/// Deterministic built-in demo, not a file-input CLI yet.
fn main {
  let text = "! Synthetic, not measured hardware\n# GHz S RI R 50\n1 0.1 0 0.8 -0.1 0.7 -0.2 0.2 0\n2 0.2 0 0.6 -0.2 0.5 -0.3 0.3 0\n"
  match @sparam.parse_touchstone(text, 2) {
    Ok(network) => println(network.to_csv())
    Err(error) =>
      println("line \{error.line}:\{error.column}: \{error.message}")
  }
}
