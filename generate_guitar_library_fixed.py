import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import os
from math import pi, sin, cos
import matplotlib.pyplot as plt

# 设置matplotlib使用英文字体，避免中文字体问题
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class GuitarSoundGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.duration = 3.0  # 每个音源的时长（秒）
        
        # 吉他标准调弦频率（Hz） - 真实吉他频率
        self.string_frequencies = {
            'E2': 82.41,   # 第6弦（最粗）
            'A': 110.00,   # 第5弦
            'D': 146.83,   # 第4弦
            'G': 196.00,   # 第3弦
            'B': 246.94,   # 第2弦
            'E4': 329.63   # 第1弦（最细）
        }
        
        # 和弦频率组成（根音、三音、五音）
        self.chord_frequencies = {
            'C_major': [261.63, 329.63, 392.00],  # C, E, G
            'G_major': [196.00, 246.94, 392.00],  # G, B, D
            'D_major': [293.66, 369.99, 440.00],  # D, F#, A
            'A_minor': [220.00, 261.63, 329.63],  # A, C, E
            'E_minor': [164.81, 196.00, 246.94],  # E, G, B
            'F_major': [174.61, 220.00, 261.63]   # F, A, C
        }

    def create_guitar_string_sound(self, frequency, string_type="nylon"):
        """Generate realistic guitar string sound"""
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration))
        
        # 基础正弦波
        fundamental = np.sin(2 * pi * frequency * t)
        
        # 谐波成分 - 模拟吉他丰富的谐波
        harmonics = []
        for i in range(2, 8):  # 2次到7次谐波
            harmonic_amp = 0.7 / i  # 谐波振幅递减
            if string_type == "steel":
                harmonic_amp *= 1.2  # 钢弦谐波更丰富
            harmonics.append(harmonic_amp * np.sin(2 * pi * frequency * i * t))
        
        # 组合所有谐波
        combined = fundamental
        for harmonic in harmonics:
            combined += harmonic
        
        # 应用吉他特有的包络（ADSR）
        envelope = self.create_guitar_envelope(t)
        combined = combined * envelope
        
        # 添加轻微的颤音效果
        vibrato_depth = 0.003
        vibrato_rate = 5.0
        vibrato = 1 + vibrato_depth * np.sin(2 * pi * vibrato_rate * t)
        combined = combined * vibrato
        
        return combined

    def create_guitar_envelope(self, t):
        """Create guitar sound envelope (Attack-Decay-Sustain-Release)"""
        attack_time = 0.02  # 起音时间
        decay_time = 0.1    # 衰减时间
        sustain_level = 0.6 # 持续电平
        release_time = 2.8  # 释音时间
        
        envelope = np.zeros_like(t)
        
        # Attack阶段
        attack_end = int(attack_time * self.sample_rate)
        if attack_end > 0:
            envelope[:attack_end] = np.linspace(0, 1, attack_end)
        
        # Decay阶段
        decay_end = int((attack_time + decay_time) * self.sample_rate)
        envelope[attack_end:decay_end] = np.linspace(1, sustain_level, decay_end - attack_end)
        
        # Sustain阶段
        sustain_end = int((self.duration - release_time) * self.sample_rate)
        envelope[decay_end:sustain_end] = sustain_level
        
        # Release阶段
        release_start = sustain_end
        envelope[release_start:] = np.linspace(sustain_level, 0, len(t) - release_start)
        
        return envelope

    def create_chord_sound(self, frequencies, chord_name):
        """Generate chord sound"""
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration))
        chord_sound = np.zeros_like(t)
        
        # 为每个频率成分生成音色并混合
        for i, freq in enumerate(frequencies):
            # 不同的弦有不同的振幅平衡
            if i == 0:  # 根音
                amplitude = 0.8
            elif i == 1:  # 三音
                amplitude = 0.6
            else:  # 五音
                amplitude = 0.7
                
            string_sound = self.create_guitar_string_sound(freq)
            # 确保长度一致
            min_len = min(len(chord_sound), len(string_sound))
            chord_sound[:min_len] += amplitude * string_sound[:min_len]
        
        # 归一化防止削波
        max_val = np.max(np.abs(chord_sound))
        if max_val > 0:
            chord_sound = chord_sound / max_val * 0.9
        
        return chord_sound

    def create_pick_noise(self):
        """Generate pick noise"""
        duration = 0.5  # 0.5秒
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 宽带噪声模拟拨片接触弦的瞬间
        noise = np.random.normal(0, 0.5, len(t))
        
        # 高频滤波模拟拨片特性
        b, a = signal.butter(4, [2000, 8000], 'bandpass', fs=self.sample_rate)
        filtered_noise = signal.lfilter(b, a, noise)
        
        # 快速衰减的包络
        envelope = np.exp(-10 * t)
        result = filtered_noise * envelope
        
        # 归一化
        result = result / np.max(np.abs(result)) * 0.7
        return result

    def create_string_slide(self):
        """Generate string slide effect"""
        duration = 1.5
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 频率从低到高滑动
        start_freq = 100
        end_freq = 800
        freq_sweep = np.linspace(start_freq, end_freq, len(t))
        
        # 生成滑音
        phase = 2 * pi * np.cumsum(freq_sweep) / self.sample_rate
        slide_sound = 0.5 * np.sin(phase)
        
        # 添加摩擦噪声
        noise = 0.3 * np.random.normal(0, 0.2, len(t))
        slide_sound += noise
        
        # 包络
        envelope = np.ones_like(t)
        fade_samples = min(100, len(t) // 10)  # 淡入淡出采样点数
        if fade_samples > 0:
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)  # 淡入
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)  # 淡出
        
        result = slide_sound * envelope
        result = result / np.max(np.abs(result)) * 0.8
        return result

    def create_harmonic(self):
        """Generate harmonic effect"""
        duration = 2.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 基础频率（A音）
        base_freq = 440.0
        
        # 强调12品泛音（2倍频）
        fundamental = 0.3 * np.sin(2 * pi * base_freq * t)
        harmonic_12th = 0.7 * np.sin(2 * pi * base_freq * 2 * t)
        harmonic_7th = 0.4 * np.sin(2 * pi * base_freq * 3 * t)
        
        combined = fundamental + harmonic_12th + harmonic_7th
        
        # 铃铛般的包络
        envelope = np.exp(-2 * t)
        result = combined * envelope
        
        result = result / np.max(np.abs(result)) * 0.9
        return result

    def save_audio(self, audio, filename, sample_rate=44100):
        """Save as WAV file"""
        try:
            # 转换为16位PCM格式
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(filename, sample_rate, audio_int16)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Save failed {filename}: {e}")

    def generate_complete_library(self):
        """Generate complete guitar sound library"""
        # 创建目录结构
        os.makedirs("guitar_samples/single_notes", exist_ok=True)
        os.makedirs("guitar_samples/chords", exist_ok=True)
        os.makedirs("guitar_samples/effects", exist_ok=True)
        
        print("Generating guitar sound library...")
        
        # 生成单音
        print("\nGenerating single notes...")
        for note_name, freq in self.string_frequencies.items():
            print(f"   Generating {note_name} string ({freq}Hz)...")
            sound = self.create_guitar_string_sound(freq)
            self.save_audio(sound, f"guitar_samples/single_notes/{note_name}.wav")
        
        # 生成和弦
        print("\nGenerating chords...")
        for chord_name, frequencies in self.chord_frequencies.items():
            print(f"   Generating {chord_name} chord...")
            chord_sound = self.create_chord_sound(frequencies, chord_name)
            self.save_audio(chord_sound, f"guitar_samples/chords/{chord_name}.wav")
        
        # 生成特效音
        print("\nGenerating effects...")
        print("   Generating pick noise...")
        pick_sound = self.create_pick_noise()
        self.save_audio(pick_sound, "guitar_samples/effects/pick_noise.wav")
        
        print("   Generating string slide...")
        slide_sound = self.create_string_slide()
        self.save_audio(slide_sound, "guitar_samples/effects/string_slide.wav")
        
        print("   Generating harmonic...")
        harmonic_sound = self.create_harmonic()
        self.save_audio(harmonic_sound, "guitar_samples/effects/harmonic.wav")
        
        print("\nGuitar sound library generation completed!")

    def analyze_and_visualize(self, audio, title):
        """Analyze and visualize generated audio (English only)"""
        plt.figure(figsize=(12, 6))
        
        # Waveform
        plt.subplot(2, 1, 1)
        display_length = min(44100, len(audio))  # Show first 1 second
        plt.plot(audio[:display_length])
        plt.title(f'{title} - Waveform')
        plt.xlabel('Samples')
        plt.ylabel('Amplitude')
        plt.grid(True)
        
        # Spectrum
        plt.subplot(2, 1, 2)
        spectrum = np.abs(np.fft.fft(audio))[:len(audio)//2]
        freqs = np.fft.fftfreq(len(audio), 1/self.sample_rate)[:len(audio)//2]
        plt.semilogy(freqs, spectrum)
        plt.title(f'{title} - Spectrum')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.xlim(0, 5000)  # Limit frequency range
        
        plt.tight_layout()
        plt.show()

# 使用示例
if __name__ == "__main__":
    try:
        # 创建生成器实例
        generator = GuitarSoundGenerator(sample_rate=44100)
        
        # 生成完整音源库
        generator.generate_complete_library()
        
        # 可选：分析和可视化示例音频
        print("\nGenerating example analysis...")
        example_sound = generator.create_guitar_string_sound(329.63)  # E4 string
        generator.analyze_and_visualize(example_sound, "E4 String Example")
        
        print("All tasks completed!")
        print("Generated sound library structure:")
        print("""
guitar_samples/
├── single_notes/          # Single note samples
│   ├── E4.wav            # High E string
│   ├── B.wav             # B string
│   ├── G.wav             # G string
│   ├── D.wav             # D string
│   ├── A.wav             # A string
│   └── E2.wav            # Low E string
├── chords/               # Chord samples
│   ├── C_major.wav       # C major chord
│   ├── G_major.wav      # G major chord
│   ├── D_major.wav      # D major chord
│   ├── A_minor.wav      # A minor chord
│   ├── E_minor.wav      # E minor chord
│   └── F_major.wav      # F major chord
└── effects/              # Effect sounds
    ├── pick_noise.wav    # Pick noise
    ├── string_slide.wav  # String slide effect
    └── harmonic.wav      # Harmonic effect
        """)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please check if dependencies are installed correctly")
