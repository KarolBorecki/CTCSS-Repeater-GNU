import numpy as np
from gnuradio import gr

class repeater_control(gr.sync_block):
    """
    Logika sterująca przemiennikiem:
    - Wejście 0: Surowe Audio (zdemodulowane)
    - Wejście 1: Detekcja CTCSS (sygnał 0.0 lub 1.0)
    - Wejście 2: Detekcja Tonu Mocy (sygnał 0.0 lub 1.0)
    
    - Wyjście 0: Audio Bramkowane (idzie do nadajnika)
    - Wyjście 1: Poziom Mocy (mnożnik dla bloku Multiply)
    """

    def __init__(self, sample_rate=48000, cooldown_seconds=2.0):
        gr.sync_block.__init__(
            self,
            name='Repeater Logic Controller',   
            in_sig=[np.float32, np.float32, np.float32],
            out_sig=[np.float32, np.float32]
        )
        
        self.sample_rate = sample_rate
        self.cooldown_samples = int(sample_rate * cooldown_seconds)
        
        self.current_gain = 0.2  # Domyślna moc
        self.high_gain = 1.0     # Maksymalna moc
        self.low_gain = 0.2      # Minimalna moc
        
        self.timer = 0           # Licznik czasu do debouncingu przełączania mocy

    def work(self, input_items, output_items):
        audio_in = input_items[0]
        ctcss_signal = input_items[1]
        power_cmd_signal = input_items[2]
        
        audio_out = output_items[0]
        gain_out = output_items[1]
        
        squelch_mask = (ctcss_signal > 0.5).astype(np.float32)
        
        audio_out[:] = audio_in * squelch_mask
        
        tone_detected = np.max(power_cmd_signal) > 0.5
        
        if self.timer > 0:
            self.timer -= len(audio_in)
        
        if tone_detected and self.timer <= 0:
            if self.current_gain == self.low_gain:
                self.current_gain = self.high_gain
            else:
                self.current_gain = self.low_gain
            
            self.timer = self.cooldown_samples
            
        gain_out[:] = self.current_gain
        
        return len(output_items[0])