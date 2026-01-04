import os
import wave
import numpy as np
import time
import platform

# 尝试导入 scipy（必需），若缺失给出提示
try:
    from scipy import signal
except Exception as e:
    raise ImportError("需要安装 scipy：pip install scipy") from e

# 可选播放库回退
_playback_method = None
if platform.system() == "Windows":
    try:
        import winsound
        _playback_method = "winsound"
    except Exception:
        _playback_method = None
else:
    try:
        import simpleaudio as sa  # type: ignore
        _playback_method = "simpleaudio"
    except Exception:
        _playback_method = None

# 生成设置
SAMPLE_RATE = 44100
DURATION = 2.5  # 秒
OUTPUT_DIR = os.path.join('assets', 'guitar_samples', 'single_notes')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 基础空弦频率（从高音弦到低音弦）
BASE_FREQS = [329.63, 246.94, 196.00, 146.83, 110.00, 82.41]  # string1..string6

# 用于更真实音色的弦参数（可按需调整）
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
    改进的 Karplus-Strong 算法，考虑拨弦激励、频率相关衰减、琴体共振与包络。
    返回 Nx2 的立体声 float 数组，幅度范围在 [-1,1]
    """
    # 保护
    if frequency <= 0:
        frequency = 1.0

    N = int(round(sample_rate / frequency))
    if N < 2:
        N = 2

    params = STRING_PARAMS[max(0, min(len(STRING_PARAMS) - 1, string_index - 1))]
    tension = params['tension']
    brightness = params['brightness']
    body_resonance = params['body_resonance']

    # 初始激励：带通滤波的白噪声，模拟拨弦位置影响频谱
    pluck_noise = np.random.uniform(-1.0, 1.0, N * 2)
    pluck_position = 0.1 + 0.8 * (fret / 20.0)
    pluck_position = float(np.clip(pluck_position, 0.1, 0.9))
    low_freq = max(50.0, 1000.0 * (1.0 - pluck_position))
    high_freq = min(sample_rate / 2.0 - 100, 8000.0 * max(0.2, brightness))

    # 设计带通滤波器（巴特沃斯）
    try:
        b, a = signal.butter(4, [low_freq / (sample_rate / 2.0), high_freq / (sample_rate / 2.0)], btype='band')
        pluck_noise = signal.filtfilt(b, a, pluck_noise)
    except Exception:
        # 如果滤波失败（边界频率问题），跳过滤波
        pass

    # 包络和裁切为缓冲长度
    pluck_env = np.linspace(1.0, 0.0, len(pluck_noise)) ** 2
    pluck_noise *= pluck_env
    excitation = pluck_noise[:N].astype(np.float64)

    # 初始化循环缓冲区
    buffer = excitation.copy()
    output_length = int(sample_rate * duration)
    output = np.zeros(output_length, dtype=np.float64)

    # 衰减基准（张力影响）
    base_decay = 0.998 - 0.002 * float(np.clip(tension, 0.0, 1.5))

    for i in range(output_length):
        pos = i % N
        output[i] = buffer[pos]

        # 加权平均以模拟色散和弦的刚度
        if pos < N - 2:
            avg = buffer[pos] * 0.6 + buffer[(pos + 1) % N] * 0.3 + buffer[(pos + 2) % N] * 0.1
        else:
            avg = 0.5 * (buffer[pos] + buffer[(pos + 1) % N])

        # 时间相关衰减（使高频更快衰减）
        time_factor = 1.0 - (0.3 * (i / output_length))
        current_decay = base_decay ** max(0.1, time_factor)
        buffer[pos] = avg * current_decay

    # 琴体共振（多个峰）
    out = output
    for k in range(3):
        freq_res = body_resonance * (0.8 + 0.25 * k)
        Q = 5.0 + 3.0 * k
        try:
            b, a = signal.iirpeak(freq_res, Q, sample_rate)
            out = signal.lfilter(b, a, out)
        except Exception:
            pass
    out = out * (1.0 + 0.12)

    # 包络（ADSR 风格）
    attack_time = 0.005
    decay_time = 0.3 + 0.2 * float(np.clip(tension, 0.0, 1.5))
    release_time = 0.5
    t = np.linspace(0, duration, output_length)
    envelope = np.ones_like(out)
    attack_samples = int(attack_time * sample_rate)
    decay_samples = int(decay_time * sample_rate)
    release_start = max(0, int(sample_rate * (duration - release_time)))

    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    if decay_samples > 0:
        start = attack_samples
        end = min(start + decay_samples, len(envelope))
        envelope[start:end] = 0.1 + (1.0 - 0.1) * np.exp(-np.linspace(0, 3, end - start))
    if release_start < len(envelope):
        release_len = len(envelope) - release_start
        envelope[release_start:] *= np.exp(-np.linspace(0, 5, release_len))

    out *= envelope

    # 轻微颤音和漂移（音高/振幅调制的简化）
    vibrato_depth = 0.002 * (1.0 + fret / 12.0)
    vibrato = 1.0 + vibrato_depth * np.sin(2 * np.pi * 5.0 * t)
    out *= vibrato

    # 立体声扩展与小混响卷积（简单实现）
    stereo_width = 0.25
    left = out * (1.0 - stereo_width * 0.5)
    right = out * (1.0 + stereo_width * 0.5)

    # 小混响脉冲响应
    reverb_len = max(1, int(0.01 * sample_rate))
    ir = np.exp(-np.linspace(0, 10, reverb_len)) * (np.random.randn(reverb_len) * 0.2)
    ir /= (np.max(np.abs(ir)) + 1e-9)

    left = np.convolve(left, ir, mode='same')
    right = np.convolve(right, ir, mode='same')

    stereo = np.column_stack((left, right))
    maxv = np.max(np.abs(stereo))
    if maxv > 0:
        stereo = stereo / maxv * 0.9

    return stereo.astype(np.float32)


def write_stereo_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """写入立体声 WAV（samples: Nx2 float32 [-1,1]）"""
    if samples.ndim == 1:
        samples = np.column_stack((samples, samples))
    samples_16 = (samples * 32767.0).astype(np.int16)
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples_16.tobytes())


def add_string_noise(sig, freq, sample_rate=SAMPLE_RATE):
    """添加高频弦噪声（轻微）"""
    length = sig.shape[0]
    noise = np.random.randn(length) * 0.003
    # 简单高通：差分作为高频成分
    hf = np.concatenate(([0.0], np.diff(noise)))
    if sig.ndim == 2:
        hf = np.column_stack((hf, hf))
    return sig + hf


def generate_all():
    print("开始生成吉他音色（improved）...")
    for s_idx, base in enumerate(BASE_FREQS, start=1):
        for fret in range(0, 11):  # 0-10 品
            freq = base * (2 ** (fret / 12.0))
            fname = f'string{s_idx}_fret{fret}.wav'
            out_path = os.path.join(OUTPUT_DIR, fname)
            print(f'生成: {out_path} 频率={freq:.2f}Hz 弦={s_idx} 品格={fret}')
            try:
                samples = improved_karplus_strong(freq, s_idx, fret, duration=DURATION, sample_rate=SAMPLE_RATE)
                samples = add_string_noise(samples, freq, SAMPLE_RATE)
                write_stereo_wav(out_path, samples, SAMPLE_RATE)
            except Exception as e:
                print(f"生成失败 {out_path}: {e}")
                # 退回到简单正弦做占位
                t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), False)
                wave_signal = 0.5 * np.sin(2 * np.pi * freq * t)
                env = np.exp(-2.0 * t)
                stereo = np.column_stack((wave_signal * env, wave_signal * env))
                write_stereo_wav(out_path, stereo, SAMPLE_RATE)


def generate_sample_chord():
    """生成并保存示例和弦（C大调示例）"""
    chord_freqs = [
        329.63 * (2 ** (3 / 12.0)),  # 1弦3品 C
        246.94,  # 2弦空弦
        196.00,  # 3弦空弦
        146.83 * (2 ** (3 / 12.0)),  # 4弦3品 C
        110.00 * (2 ** (2 / 12.0)),  # 5弦2品 B
        82.41 * (2 ** (3 / 12.0)),  # 6弦3品 C
    ]

    chord_samples = []
    for i, freq in enumerate(chord_freqs):
        samples = improved_karplus_strong(freq, 2, 0, duration=4.0, sample_rate=SAMPLE_RATE)
        chord_samples.append(samples)

    min_len = min([len(s) for s in chord_samples])
    mixed = np.zeros((min_len, 2), dtype=np.float32)
    for s in chord_freqs:
        pass
    for s in chord_samples:
        mixed[:min_len] += s[:min_len]

    mixed = mixed / len(chord_samples)
    mixed = mixed / (np.max(np.abs(mixed)) + 1e-9) * 0.8
    chord_path = os.path.join(OUTPUT_DIR, 'chord_C_major.wav')
    write_stereo_wav(chord_path, mixed, SAMPLE_RATE)
    print(f"已生成示例和弦: {chord_path}")
    return chord_path


def play_wav(path):
    """播放 wav 文件（优先 winsound/simpleaudio）"""
    if not os.path.exists(path):
        print("播放失败：文件不存在", path)
        return
    if _playback_method == "winsound":
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception:
            pass
    elif _playback_method == "simpleaudio":
        try:
            import simpleaudio as sa  # type: ignore
            wave_read = wave.open(path, 'rb')
            data = wave_read.readframes(wave_read.getnframes())
            play_obj = sa.play_buffer(data, wave_read.getnchannels(), wave_read.getsampwidth(), wave_read.getframerate())
            return play_obj
        except Exception:
            pass

    print("未检测到可用的音频播放库。若想要自动播放，请安装 'simpleaudio'（跨平台）或在 Windows 上使用自带 winsound。")


if __name__ == '__main__':
    start = time.time()
    generate_all()
    chord = generate_sample_chord()
    # 播放示例和弦（异步播放）
    play_wav(chord)
    print('生成完成，音色保存在:', OUTPUT_DIR)
    print('耗时: {:.1f}s'.format(time.time() - start))
