import os
import wave
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
import random

# 生成设置
SAMPLE_RATE = 44100
DURATION = 2.5  # 秒
OUTPUT_DIR = os.path.join('assets', 'guitar_samples', 'single_notes')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 基础空弦频率（EADGBE标准调弦）
BASE_FREQS = [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]  # 从高音弦到低音弦

# 吉他弦的物理参数（不同弦的特性不同）
STRING_PARAMS = [
    {'tension': 0.8, 'brightness': 0.9, 'body_resonance': 3000},  # 高音E弦
    {'tension': 0.85, 'brightness': 0.85, 'body_resonance': 2500},  # B弦
    {'tension': 0.9, 'brightness': 0.8, 'body_resonance': 2000},  # G弦
    {'tension': 0.85, 'brightness': 0.75, 'body_resonance': 1800},  # D弦
    {'tension': 0.8, 'brightness': 0.7, 'body_resonance': 1500},  # A弦
    {'tension': 0.75, 'brightness': 0.65, 'body_resonance': 1200},  # 低音E弦
]

def improved_karplus_strong(frequency, string_index, fret, duration=DURATION, sample_rate=SAMPLE_RATE):
    """
    改进的Karplus-Strong算法，考虑更多吉他物理特性
    """
    # 计算延迟线长度
    N = int(round(sample_rate / frequency))
    if N < 2:
        N = 2
    
    # 获取当前弦的参数
    params = STRING_PARAMS[string_index-1]
    tension = params['tension']
    brightness = params['brightness']
    
    # 1. 初始激励信号 - 更真实的拨弦噪声
    # 使用带通滤波的白噪声模拟拨弦瞬间
    pluck_noise = np.random.uniform(-1, 1, N*2)
    
    # 模拟拨弦位置的频谱特性（靠近琴桥=明亮，靠近琴颈=温暖）
    # 按品格位置调整滤波
    pluck_position = 0.1 + 0.8 * (fret / 20)  # 高品位更靠近琴颈
    pluck_position = min(max(pluck_position, 0.1), 0.9)
    
    # 设计一个更适合吉他拨弦的滤波器
    low_freq = 1000 * (1.0 - pluck_position)  # 拨弦位置影响高频
    high_freq = 8000 * brightness
    
    # 使用巴特沃斯带通滤波器
    b, a = signal.butter(4, [low_freq/(sample_rate/2), high_freq/(sample_rate/2)], btype='band')
    pluck_noise = signal.filtfilt(b, a, pluck_noise)
    
    # 添加轻微的非线性特性 - 弦的初始位移
    pluck_env = np.linspace(1, 0, N*2) ** 2
    pluck_noise *= pluck_env
    
    # 取前N个样本作为初始激励
    excitation = pluck_noise[:N]
    
    # 2. 循环滤波器 - 模拟弦的物理特性
    buffer = excitation.copy()
    output_length = int(sample_rate * duration)
    output = np.zeros(output_length)
    
    # 随时间变化的衰减系数（模拟弦振动衰减）
    t = np.linspace(0, duration, output_length)
    base_decay = 0.998 - 0.002 * tension  # 张力大的弦衰减慢
    
    # 高频衰减比低频快（更真实）
    high_freq_decay = 0.99
    low_freq_decay = 0.999
    
    # 3. 主处理循环
    for i in range(output_length):
        # 当前读取位置
        pos = i % N
        
        # 输出当前样本
        output[i] = buffer[pos]
        
        # 计算滤波后的值（模拟弦的色散）
        # 使用加权平均而不是简单平均，模拟弦的刚度
        if pos < N-2:
            # 考虑相邻样本的影响
            avg = (buffer[pos] * 0.6 + 
                   buffer[(pos+1) % N] * 0.3 + 
                   buffer[(pos+2) % N] * 0.1)
        else:
            avg = (buffer[pos] + buffer[(pos+1) % N]) * 0.5
        
        # 应用衰减（高频衰减更快）
        # 简单的频率相关衰减模拟
        current_decay = base_decay
        if i % 2 == 0:  # 简单模拟高频成分
            current_decay = high_freq_decay
        else:
            current_decay = low_freq_decay
        
        # 随时间增加衰减
        time_factor = 1.0 - (0.3 * (i / output_length))
        current_decay = base_decay ** time_factor
        
        # 更新缓冲区
        buffer[pos] = avg * current_decay
    
    # 4. 吉他琴体共鸣模拟
    # 添加琴身共振峰
    body_resonance = params['body_resonance']
    resonance_gain = 0.3  # 共振强度
    
    # 设计共振滤波器
    for i in range(3):
        freq = body_resonance * (0.8 + 0.4 * i)  # 多个共振峰
        Q = 5.0 + 3.0 * i  # 品质因数
        
        # 使用二阶IIR滤波器模拟共振
        b, a = signal.iirpeak(freq, Q, sample_rate)
        output = signal.lfilter(b, a, output) * (1.0 + resonance_gain * 0.3)
    
    # 5. 动态包络
    # 更真实的吉他包络：快速起音，指数衰减，带有轻微释放
    attack_time = 0.005  # 5ms起音
    decay_time = 0.3 + 0.2 * tension  # 张力影响衰减时间
    sustain_level = 0.1
    release_time = 0.5
    
    # 生成ADSR包络
    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_samples = int(release_time * sample_rate)
    
    envelope = np.ones_like(output)
    
    # 起音阶段
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # 衰减阶段
    if decay_samples > 0:
        start = attack_samples
        end = min(start + decay_samples, len(envelope))
        decay_curve = np.exp(-np.linspace(0, 3, end-start))
        envelope[start:end] = sustain_level + (1 - sustain_level) * decay_curve
    
    # 释放阶段
    release_start = min(int(sample_rate * (duration - release_time)), len(envelope))
    if release_start < len(envelope):
        release_len = len(envelope) - release_start
        release_curve = np.exp(-np.linspace(0, 5, release_len))
        envelope[release_start:] = envelope[release_start] * release_curve
    
    # 应用包络
    output *= envelope
    
    # 6. 添加微妙的调制（颤音、音高漂移）
    # 轻微的颤音
    vibrato_depth = 0.002 * (1 + fret/12)  # 高品位颤音更明显
    vibrato_rate = 5.0  # Hz
    vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
    
    # 轻微的音高漂移（真实弦的特性）
    drift = 1.0 + 0.001 * np.sin(2 * np.pi * 0.3 * t + np.random.random())
    
    # 应用调制
    mod_signal = vibrato * drift
    output = signal.resample(output, len(output))  # 简化处理
    
    # 7. 立体声扩展（轻微左右声道差异）
    stereo_width = 0.3
    left = output * (1 - stereo_width * 0.5)
    right = output * (1 + stereo_width * 0.5)
    
    # 添加轻微的房间混响（卷积简单脉冲响应）
    room_size = 0.1  # 小房间
    reverb_length = int(0.01 * sample_rate)  # 10ms混响
    reverb_ir = np.exp(-np.linspace(0, 10, reverb_length)) * np.random.randn(reverb_length)
    reverb_ir /= np.max(np.abs(reverb_ir))
    
    # 应用混响
    left = np.convolve(left, reverb_ir, mode='same')
    right = np.convolve(right, reverb_ir, mode='same')
    
    # 组合成立体声
    stereo_output = np.column_stack((left, right))
    
    # 归一化
    max_val = np.max(np.abs(stereo_output))
    if max_val > 0:
        stereo_output = stereo_output / max_val * 0.9  # 留有余量
    
    return stereo_output

def add_string_noise(signal, freq, sample_rate):
    """
    添加弦摩擦噪声（手指按弦、拨弦噪声）
    """
    noise_level = 0.01  # 噪声水平
    t = np.linspace(0, len(signal)/sample_rate, len(signal))
    
    # 高频摩擦噪声
    noise = np.random.randn(len(signal)) * noise_level
    # 滤波到高频区域
    b, a = signal.butter(4, 2000/(sample_rate/2), btype='high')
    noise = signal.filtfilt(b, a, noise)
    
    # 衰减包络
    env = np.exp(-5 * t)
    noise *= env[:, np.newaxis]
    
    return signal + noise

def write_stereo_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """
    写入立体声WAV文件
    """
    # 转换为16-bit
    samples_16bit = (samples * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(2)  # 立体声
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(samples_16bit.tobytes())

def generate_all():
    """
    生成所有音符
    """
    print("开始生成吉他音色...")
    print("这可能需要一些时间，请耐心等待...")
    
    for s_idx, base in enumerate(BASE_FREQS, start=1):
        for fret in range(0, 12):  # 生成前12个品格
            # 计算频率
            freq = base * (2 ** (fret/12))
            
            # 生成文件名
            fname = f'string{s_idx}_fret{fret}.wav'
            out_path = os.path.join(OUTPUT_DIR, fname)
            
            print(f'生成: {out_path} 频率={freq:.2f}Hz 弦={s_idx} 品格={fret}')
            
            # 生成音色
            try:
                samples = improved_karplus_strong(freq, s_idx, fret, duration=DURATION)
                
                # 添加弦噪声
                samples = add_string_noise(samples, freq, SAMPLE_RATE)
                
                # 写入文件
                write_stereo_wav(out_path, samples)
                
            except Exception as e:
                print(f"生成失败 {out_path}: {e}")
                # 生成一个简单的正弦波作为备选
                t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
                wave_signal = 0.5 * np.sin(2 * np.pi * freq * t)
                env = np.exp(-2.0 * t)
                wave_signal *= env
                
                # 立体声
                stereo = np.column_stack((wave_signal, wave_signal))
                write_stereo_wav(out_path, stereo)

def generate_sample_chord():
    """
    生成一个示例和弦来测试音色
    """
    # C大调和弦：C(1弦3品), E(2弦空弦), G(3弦空弦), C(4弦3品), E(5弦2品), C(6弦3品)
    chord_freqs = [
        329.63 * (2 ** (3/12)),  # 1弦3品 C
        246.94,                  # 2弦空弦 B
        196.00,                  # 3弦空弦 G
        146.83 * (2 ** (3/12)),  # 4弦3品 C
        110.00 * (2 ** (2/12)),  # 5弦2品 B
        82.41 * (2 ** (3/12)),   # 6弦3品 C
    ]
    
    chord_samples = []
    
    for i, freq in enumerate(chord_freqs):
        print(f"生成和弦音符 {i+1}: {freq:.2f}Hz")
        # 使用第二弦的参数作为折中
        samples = improved_karplus_strong(freq, 2, 0, duration=4.0)
        chord_samples.append(samples)
    
    # 混合所有音符
    # 对齐长度
    min_len = min([len(s) for s in chord_samples])
    mixed = np.zeros((min_len, 2))
    
    for s in chord_samples:
        mixed[:min_len] += s[:min_len]
    
    # 归一化
    mixed = mixed / len(chord_samples)
    mixed = mixed / np.max(np.abs(mixed)) * 0.8
    
    # 写入和弦示例
    chord_path = os.path.join(OUTPUT_DIR, 'chord_C_major.wav')
    write_stereo_wav(chord_path, mixed)
    print(f"已生成示例和弦: {chord_path}")

if __name__ == '__main__':
    # 安装必要的库（如果未安装）
    try:
        import scipy
    except ImportError:
        print("需要安装scipy库，请运行: pip install scipy")
        exit(1)
    
    # 生成单音
    generate_all()
    
    # 生成示例和弦
    generate_sample_chord()
    
    print('\n生成完成！')
    print('音色已保存在:', OUTPUT_DIR)
    print('可以试听生成的 chord_C_major.wav 来感受整体效果')
    
    # 生成一个简单的测试文件列表
    test_list = os.path.join(OUTPUT_DIR, 'test_samples.txt')
    with open(test_list, 'w') as f:
        f.write("生成的测试音色列表:\n")
        for i in range(1, 7):
            for j in [0, 3, 5, 7, 12]:
                fname = f'string{i}_fret{j}.wav'
                if os.path.exists(os.path.join(OUTPUT_DIR, fname)):
                    f.write(f"{fname}\n")