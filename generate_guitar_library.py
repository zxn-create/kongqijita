import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import os
from math import pi
import matplotlib.pyplot as plt

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
        """生成真实的吉他弦音色"""
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
        
        # 归一化防止削波
        max_val = np.max(np.abs(combined))
        if max_val > 0:
            combined = combined / max_val * 0.9
        
        return combined

    def create_guitar_envelope(self, t):
        """创建吉他音色的包络（Attack-Decay-Sustain-Release）"""
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
        if decay_end > attack_end:
            envelope[attack_end:decay_end] = np.linspace(1, sustain_level, decay_end - attack_end)
        
        # Sustain阶段
        sustain_end = int((self.duration - release_time) * self.sample_rate)
        if sustain_end > decay_end:
            envelope[decay_end:sustain_end] = sustain_level
        
        # Release阶段
        release_start = sustain_end
        if len(t) > release_start:
            envelope[release_start:] = np.linspace(sustain_level, 0, len(t) - release_start)
        
        return envelope

    def create_chord_sound(self, frequencies, chord_name):
        """生成和弦音色"""
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
        """生成拨片噪音"""
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
        max_val = np.max(np.abs(result))
        if max_val > 0:
            result = result / max_val * 0.7
        return result

    def create_string_slide(self):
        """生成滑弦效果"""
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
        # 归一化
        max_val = np.max(np.abs(result))
        if max_val > 0:
            result = result / max_val * 0.8
        return result

    def create_harmonic(self):
        """生成泛音效果"""
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
        
        # 归一化
        max_val = np.max(np.abs(result))
        if max_val > 0:
            result = result / max_val * 0.9
        return result

    def save_audio(self, audio, filename):
        """保存为WAV文件"""
        try:
            # 转换为16位PCM格式
            audio_int16 = (audio * 32767).astype(np.int16)
            wavfile.write(filename, self.sample_rate, audio_int16)
            print(f"✅ 已保存: {filename}")
        except Exception as e:
            print(f"❌ 保存失败 {filename}: {e}")

    def analyze_and_visualize_simple(self, audio, title):
        """简化的分析和可视化（避免librosa依赖）"""
        plt.figure(figsize=(12, 6))
        
        # 波形图
        plt.subplot(2, 1, 1)
        display_length = min(44100, len(audio))  # 显示前1秒
        plt.plot(audio[:display_length])
        plt.title(f'{title} - 波形')
        plt.xlabel('采样点')
        plt.ylabel('振幅')
        plt.grid(True)
        
        # 频谱图
        plt.subplot(2, 1, 2)
        # 使用FFT计算频谱
        spectrum = np.abs(np.fft.fft(audio))[:len(audio)//2]
        freqs = np.fft.fftfreq(len(audio), 1/self.sample_rate)[:len(audio)//2]
        plt.semilogy(freqs, spectrum)
        plt.title(f'{title} - 频谱')
        plt.xlabel('频率 (Hz)')
        plt.ylabel('振幅')
        plt.grid(True)
        plt.xlim(0, 5000)  # 限制频率范围显示
        
        plt.tight_layout()
        plt.show()

    def generate_complete_library(self):
        """生成完整的吉他音源库"""
        # 创建目录结构
        os.makedirs("guitar_samples/single_notes", exist_ok=True)
        os.makedirs("guitar_samples/chords", exist_ok=True)
        os.makedirs("guitar_samples/effects", exist_ok=True)
        
        print("🎸 开始生成吉他音源库...")
        
        # 生成单音
        print("\n🎵 生成单音采样...")
        for note_name, freq in self.string_frequencies.items():
            print(f"   生成 {note_name} 弦 ({freq}Hz)...")
            try:
                sound = self.create_guitar_string_sound(freq)
                self.save_audio(sound, f"guitar_samples/single_notes/{note_name}.wav")
            except Exception as e:
                print(f"❌ 生成 {note_name} 失败: {e}")
        
        # 生成和弦
        print("\n🎶 生成和弦采样...")
        for chord_name, frequencies in self.chord_frequencies.items():
            print(f"   生成 {chord_name} 和弦...")
            try:
                chord_sound = self.create_chord_sound(frequencies, chord_name)
                self.save_audio(chord_sound, f"guitar_samples/chords/{chord_name}.wav")
            except Exception as e:
                print(f"❌ 生成 {chord_name} 失败: {e}")
        
        # 生成特效音
        print("\n✨ 生成特效音...")
        effects = [
            ("拨片噪音", self.create_pick_noise, "pick_noise.wav"),
            ("滑弦效果", self.create_string_slide, "string_slide.wav"),
            ("泛音效果", self.create_harmonic, "harmonic.wav")
        ]
        
        for effect_name, effect_func, filename in effects:
            print(f"   生成{effect_name}...")
            try:
                effect_sound = effect_func()
                self.save_audio(effect_sound, f"guitar_samples/effects/{filename}")
            except Exception as e:
                print(f"❌ 生成{effect_name}失败: {e}")
        
        print("\n🎉 吉他音源库生成完成！")

# 使用示例
if __name__ == "__main__":
    try:
        # 创建生成器实例
        generator = GuitarSoundGenerator(sample_rate=44100)
        
        # 生成完整音源库
        generator.generate_complete_library()
        
        # 可选：分析和可视化示例音频（简化版）
        print("\n📊 生成示例分析...")
        example_sound = generator.create_guitar_string_sound(329.63)  # E4弦
        generator.analyze_and_visualize_simple(example_sound, "E4弦示例")
        
        print("🎸 所有任务完成！")
        print("📁 生成的音源库结构：")
        print("""
guitar_samples/
├── single_notes/          # 单音采样
│   ├── E4.wav            # 高音E弦
│   ├── B.wav             # B弦
│   ├── G.wav             # G弦
│   ├── D.wav             # D弦
│   ├── A.wav             # A弦
│   └── E2.wav            # 低音E弦
├── chords/               # 和弦采样
│   ├── C_major.wav       # C大和弦
│   ├── G_major.wav      # G大和弦
│   ├── D_major.wav      # D大和弦
│   ├── A_minor.wav      # A小调和弦
│   ├── E_minor.wav      # E小调和弦
│   └── F_major.wav      # F大和弦
└── effects/              # 特效音
    ├── pick_noise.wav    # 拨片噪音
    ├── string_slide.wav  # 滑弦效果
    └── harmonic.wav      # 泛音效果
        """)
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        print("💡 建议检查依赖库安装是否正确")
