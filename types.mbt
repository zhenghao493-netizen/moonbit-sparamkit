///| Source representation; normalized samples always contain real/imaginary pairs.
pub(all) enum DataFormat {
  RI
  MA
  DB
} derive(Show, Eq)

///|
pub(all) enum FrequencyUnit {
  Hz
  KHz
  MHz
  GHz
} derive(Show, Eq)

///|
pub(all) enum ErrorCode {
  UnsupportedPorts
  InputLimit
  TokenLimit
  LineTokenLimit
  SampleLimit
  MissingOptions
  DuplicateOptions
  InvalidOption
  UnsupportedParameter
  UnsupportedVersion
  InvalidNumber
  NumericRange
  InvalidReference
  InvalidMagnitude
  InvalidFrequency
  FrequencyOrder
  ExtraFields
  IncompleteRecord
  NoData
} derive(Show, Eq)

///| Positions are one-based. Column counts Unicode characters, not encoded bytes.
pub(all) struct Diagnostic {
  code : ErrorCode
  line : Int
  column : Int
  message : String
} derive(Show)

///|
pub(all) struct Complex {
  re : Double
  im : Double
} derive(Show)

///| Entries use Touchstone two-port order: S11, S21, S12, S22.
pub(all) struct Sample {
  frequency_hz : Double
  values : Array[Complex]
} derive(Show)

///| Caller-created values are not automatically validated; parser results are.
pub(all) struct Network {
  ports : Int
  reference_ohms : Double
  source_unit : FrequencyUnit
  source_format : DataFormat
  samples : Array[Sample]
} derive(Show)

///|
struct Token {
  text : String
  line : Int
  column : Int
}

///|
struct Options {
  unit : FrequencyUnit
  format : DataFormat
  reference : Double
}

///|
fn diagnostic(code : ErrorCode, line : Int, column : Int, message : String) -> Diagnostic {
  { code, line, column, message }
}

///|
fn finite(value : Double) -> Bool {
  !value.is_nan() && !value.is_inf()
}

///|
fn FrequencyUnit::scale(self : FrequencyUnit) -> Double {
  match self {
    Hz => 1.0
    KHz => 1000.0
    MHz => 1000000.0
    GHz => 1000000000.0
  }
}

///| Ports are one-based: get_s(0, 2, 1) retrieves S21 at the first frequency.
pub fn Network::get_s(self : Network, sample_index : Int, output_port : Int, input_port : Int) -> Complex? {
  if self.ports != 1 && self.ports != 2 { return None }
  if output_port < 1 || output_port > self.ports || input_port < 1 || input_port > self.ports {
    return None
  }
  match self.samples.get(sample_index) {
    None => None
    Some(sample) => sample.values.get((input_port - 1) * self.ports + output_port - 1)
  }
}

///|
pub fn Complex::magnitude(self : Complex) -> Double {
  @math.hypot(self.re, self.im)
}

///| Zero magnitude has no finite dB value. Invalid caller-created values return None.
pub fn Complex::magnitude_db(self : Complex) -> Double? {
  let amplitude = self.magnitude()
  if !finite(amplitude) || amplitude <= 0.0 { return None }
  Some(20.0 * @math.log10(amplitude))
}

///| Phase is undefined for exactly zero; angles are returned in degrees.
pub fn Complex::phase_degrees(self : Complex) -> Double? {
  if !finite(self.re) || !finite(self.im) || (self.re == 0.0 && self.im == 0.0) {
    return None
  }
  Some(@math.atan2(self.im, self.re) * (180.0 / @math.PI))
}
