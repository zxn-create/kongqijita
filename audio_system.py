import pygame
import numpy as np
import os
from typing import Dict, List, Optional
import utils

class AudioSystem:
    """高级音频处理系统"""
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = utils.load_config()['audio']
            
        self.config = config
        self.samples = {}
        self.channels = {}
        self.effects = {}
        self._volume = config.get('volume', 0.7)
        
        # 初始化pygame mixer
        pygame.mixer.init(
            frequency=config['sample_rate'],
            size=-16,
            channels=config['channels'],
            buffer=config['buffer_size']
        )
        
        self.load_samples()
    
    def load_samples(self):
        """加载所有音频样本"""
        base_path = "assets/guitar_samples"
        
        # 加载单音
        single_notes_path = os.path.join(base_path, "single_notes")
        # 兼容：加载预命名的 stringX_fretY.wav 文件（0-10品，6弦）
        for s in range(1, 7):
            for f in range(0, 11):
                fname = f"string{s}_fret{f}.wav"
                file_path = os.path.join(single_notes_path, fname)
                key = f"string{s}_fret{f}"
                if os.path.exists(file_path):
                    try:
                        self.samples[key] = pygame.mixer.Sound(file_path)
                    except Exception:
                        print(f"Warning: 无法加载样本 {file_path}")
                else:
                    # 缺失样本时不立刻创建，以免阻塞，使用警告
                    print(f"Warning: Sample file {file_path} not found")
        
        # 加载和弦
        chords_path = os.path.join(base_path, "chords")
        for chord in ["C_major", "G_major", "D_major", "A_minor", "E_minor", "F_major"]:
            file_path = os.path.join(chords_path, f"{chord}.wav")
            if os.path.exists(file_path):
                self.samples[chord] = pygame.mixer.Sound(file_path)
            else:
                print(f"Warning: Chord file {file_path} not found")
        
        # 加载特效
        effects_path = os.path.join(base_path, "effects")
        for effect in ["pick_noise", "string_slide", "harmonic"]:
            file_path = os.path.join(effects_path, f"{effect}.wav")
            if os.path.exists(file_path):
                self.effects[effect] = pygame.mixer.Sound(file_path)

    def play_string_fret(self, string_number: int, fret: int, volume: float = None):
        """按照命名约定播放指定弦与品位的样本（例如 string1_fret0.wav）。"""
        if volume is None:
            volume = self.get_volume()

        key = f"string{string_number}_fret{fret}"
        if key in self.samples:
            try:
                snd = self.samples[key]
                snd.set_volume(volume)
                snd.play()
            except Exception as e:
                print(f"播放样本失败 {key}: {e}")
        else:
            print(f"样本未找到: {key}")
    
    def create_default_sample(self, frequency: float, duration: float) -> pygame.mixer.Sound:
        """创建默认音频样本（正弦波）"""
        sample_rate = self.config['sample_rate']
        frames = int(duration * sample_rate)
        
        # 生成正弦波
        t = np.linspace(0, duration, frames, False)
        wave = np.sin(2 * np.pi * frequency * t)
        
        # 添加包络
        envelope = np.ones(frames)
        attack = int(0.1 * frames)
        decay = int(0.2 * frames)
        release = int(0.3 * frames)
        
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[attack:attack+decay] = np.linspace(1, 0.7, decay)
        envelope[-release:] = np.linspace(0.7, 0, release)
        
        wave = wave * envelope
        
        # 转换为pygame声音
        wave = (wave * 32767).astype(np.int16)
        return pygame.mixer.Sound(buffer=wave)
    
    def play_note(self, note: str, volume: float = None):
        """播放单个音符"""
        if volume is None:
            try:
                volume = pygame.mixer.music.get_volume()
            except Exception:
                volume = self.config.get('volume', 0.7)

        if note in self.samples:
            self.samples[note].set_volume(volume)
            self.samples[note].play()
    
    def play_chord(self, chord: str, volume: float = None):
        """播放和弦"""
        def _get_default_volume():
            try:
                return pygame.mixer.music.get_volume()
            except Exception:
                return self.config.get('volume', 0.7)

        if volume is None:
            volume = _get_default_volume()

        if chord in self.samples:
            # 停止同名正在播放的通道
            if chord in self.channels and self.channels[chord] is not None:
                try:
                    self.channels[chord].stop()
                except Exception:
                    pass

            # play() 返回 Channel 对象
            channel = self.samples[chord].play()
            if channel is not None:
                try:
                    channel.set_volume(volume)
                    self.channels[chord] = channel
                except Exception:
                    pass
            else:
                # 如果返回 None，则使用 sample 的 set_volume（部分平台）
                try:
                    self.samples[chord].set_volume(volume)
                except Exception:
                    pass
    
    def play_effect(self, effect: str, volume: float = 0.5):
        """播放特效音"""
        if effect in self.effects:
            self.effects[effect].set_volume(volume)
            self.effects[effect].play()
    
    def stop_all(self):
        """停止所有音频"""
        # 停止已记录的通道
        for key, ch in list(self.channels.items()):
            try:
                if ch is not None:
                    ch.stop()
            except Exception:
                pass
        self.channels.clear()
        try:
            pygame.mixer.stop()
        except Exception:
            pass
    
    def set_volume(self, volume: float):
        """设置主音量"""
        try:
            pygame.mixer.music.set_volume(volume)
        except Exception:
            pass
        # 保存内部音量并更新正在播放的通道
        self._volume = volume
        for key, ch in list(self.channels.items()):
            try:
                if ch is not None:
                    ch.set_volume(volume)
            except Exception:
                # 有些平台返回 None 或不支持 set_volume
                try:
                    if key in self.samples:
                        self.samples[key].set_volume(volume)
                except Exception:
                    pass
    
    def get_volume(self) -> float:
        """获取当前音量"""
        try:
            return pygame.mixer.music.get_volume()
        except Exception:
            return getattr(self, '_volume', self.config.get('volume', 0.7))
