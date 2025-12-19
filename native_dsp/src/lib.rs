use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1};
use std::f32::consts::PI;

#[derive(Clone)]
struct BiquadFilter {
    b0: f32, b1: f32, b2: f32,
    a1: f32, a2: f32,
    x1: f32, x2: f32,
    y1: f32, y2: f32,
}

impl BiquadFilter {
    fn new() -> Self {
        BiquadFilter {
            b0: 1.0, b1: 0.0, b2: 0.0,
            a1: 0.0, a2: 0.0,
            x1: 0.0, x2: 0.0,
            y1: 0.0, y2: 0.0,
        }
    }

    fn set_peaking_eq(&mut self, freq: f32, q: f32, gain_db: f32, sample_rate: f32) {
        let omega = 2.0 * PI * freq / sample_rate;
        let alpha = omega.sin() / (2.0 * q);
        let a = 10.0f32.powf(gain_db / 40.0);
        
        let cos_w = omega.cos();
        let alpha_a = alpha * a;
        let alpha_div_a = alpha / a;

        let b0 = 1.0 + alpha_a;
        let b1 = -2.0 * cos_w;
        let b2 = 1.0 - alpha_a;
        let a0 = 1.0 + alpha_div_a;
        let a1 = -2.0 * cos_w;
        let a2 = 1.0 - alpha_div_a;

        self.b0 = b0 / a0;
        self.b1 = b1 / a0;
        self.b2 = b2 / a0;
        self.a1 = a1 / a0;
        self.a2 = a2 / a0;
    }

    fn process(&mut self, input: f32) -> f32 {
        let output = self.b0 * input + self.b1 * self.x1 + self.b2 * self.x2
                    - self.a1 * self.y1 - self.a2 * self.y2;
        
        self.x2 = self.x1;
        self.x1 = input;
        self.y2 = self.y1;
        self.y1 = output;
        
        output
    }
}

#[pyclass]
struct Equalizer {
    filters: Vec<BiquadFilter>,
    sample_rate: f32,
    frequencies: Vec<f32>,
    gains: Vec<f32>,
    q_values: Vec<f32>,
}

#[pymethods]
impl Equalizer {
    #[new]
    fn new(sample_rate: f32) -> Self {
        // Default 10-band EQ frequencies (standard octave spacing)
        let frequencies = vec![
            31.5, 63.0, 125.0, 250.0, 500.0,
            1000.0, 2000.0, 4000.0, 8000.0, 16000.0
        ];
        let num_bands = frequencies.len();
        
        Equalizer {
            filters: vec![BiquadFilter::new(); num_bands],
            sample_rate,
            frequencies,
            gains: vec![0.0; num_bands],
            q_values: vec![1.41; num_bands], // Q = 1.41 for standard octave bands
        }
    }

    fn set_gains(&mut self, gains: Vec<f32>) {
        if gains.len() == self.gains.len() {
            self.gains = gains;
            for i in 0..self.filters.len() {
                self.filters[i].set_peaking_eq(
                    self.frequencies[i],
                    self.q_values[i],
                    self.gains[i],
                    self.sample_rate
                );
            }
        }
    }

    fn process_audio(&mut self, py: Python<'_>, input: PyReadonlyArray1<f32>) -> PyResult<Py<PyArray1<f32>>> {
        let data = input.as_slice().unwrap();
        let mut output = Vec::with_capacity(data.len());
        
        for &sample in data {
            let mut processed = sample;
            for filter in &mut self.filters {
                processed = filter.process(processed);
            }
            output.push(processed);
        }
        
        let array = PyArray1::<f32>::from_slice_bound(py, &output);
        Ok(array.into())
    }

    fn reset(&mut self) {
        for filter in &mut self.filters {
            *filter = BiquadFilter::new();
        }
        self.set_gains(vec![0.0; self.gains.len()]);
    }
}

#[pymodule]
fn native_dsp(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Equalizer>()?;
    Ok(())
}
