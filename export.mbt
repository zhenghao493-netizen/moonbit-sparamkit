///| Long-form CSV, normalized to Hz and real/imaginary values. No user text enters
/// cells. Reference impedance is repeated so exported values retain their context.
pub fn Network::to_csv(self : Network) -> String {
  let rows = ["frequency_hz,reference_ohms,output_port,input_port,re,im"]
  for sample in self.samples {
    for input_port = 1; input_port <= self.ports; input_port = input_port + 1 {
      for output_port = 1; output_port <= self.ports; output_port = output_port + 1 {
        match sample.values.get((input_port - 1) * self.ports + output_port - 1) {
          Some(value) => rows.push("\{sample.frequency_hz},\{self.reference_ohms},\{output_port},\{input_port},\{value.re},\{value.im}")
          None => ()
        }
      }
    }
  }
  rows.join("\n") + "\n"
}
