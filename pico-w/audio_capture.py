import machine
import array

class AudioCapture:
    def __init__(self, pin=26, sample_rate=16000):
        self.adc = machine.ADC(pin)
        self.sample_rate = sample_rate
    
    def record(self, duration_ms=1000):
        samples = array.array('H', [0] * (self.sample_rate * duration_ms // 1000))
        return samples
    