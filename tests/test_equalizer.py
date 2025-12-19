import unittest
import numpy as np
from audio_processing.processors import Equalizer

class TestEqualizer(unittest.TestCase):

    def setUp(self):
        self.sample_rate = 48000
        self.bands = 10
        self.equalizer = Equalizer(sample_rate=self.sample_rate, bands=self.bands)

    def test_initialization(self):
        self.assertEqual(self.equalizer.sample_rate, self.sample_rate)
        self.assertEqual(self.equalizer.bands, self.bands)
        self.assertTrue(self.equalizer.enabled)

    def test_process_disabled(self):
        self.equalizer.disable()
        data = np.ones((1024,))
        processed = self.equalizer.process(data)
        np.testing.assert_array_equal(data, processed)

    def test_process_enabled(self):
        self.equalizer.enable()
        data = np.ones((1024,))
        processed = self.equalizer.process(data)
        self.assertEqual(processed.shape, data.shape)

    def test_error_handling(self):
        self.equalizer._native = None  # Simulate native backend failure
        data = np.ones((1024,))
        processed = self.equalizer.process(data)
        self.assertEqual(processed.shape, data.shape)

if __name__ == "__main__":
    unittest.main()
