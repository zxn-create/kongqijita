import streamlit as st
import cv2
import pygame
import numpy as np
import time
import sys
import os
import random
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont

# 删除对 OpenGL 的尝试导入，直接设置为不可用
HAS_OPENGL = False
Guitar3DEngine = None

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hand_tracker1 import HandTracker
from gesture_analyzer1 import GestureAnalyzer
from audio_system import AudioSystem
import utils

class AirGuitarApp:
    """空气吉他主应用程序"""
    
    def __init__(self):
        self.config = utils.load_config()
        self.setup_components()
        
        # 状态变量
        self.is_running = False
        self.current_chord = "none"
        self.prev_hand_data = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.button_counter = 0
        self.chord_history = []
        self.debug_info = ""
        
        # 粒子特效系统
        self.particles = []
        self.last_particle_time = time.time()
        
        # 吉他弦数据
        self.strings_data = {
            'E_low': {'wave': [], 'color': (255, 200, 50), 'note': 'E2', 'active': False},
            'A': {'wave': [], 'color': (255, 150, 50), 'note': 'A2', 'active': False},
            'D': {'wave': [], 'color': (255, 100, 100), 'note': 'D3', 'active': False},
            'G': {'wave': [], 'color': (100, 255, 100), 'note': 'G3', 'active': False},
            'B': {'wave': [], 'color': (100, 200, 255), 'note': 'B3', 'active': False},
            'E_high': {'wave': [], 'color': (200, 150, 255), 'note': 'E4', 'active': False}
        }
        
        # 和弦到弦激活的映射
        self.chord_string_mapping = {
            'C_major': ['E_low', 'C', 'E_high'],
            'G_major': ['G', 'B', 'D', 'G', 'B', 'G'],
            'D_major': ['D', 'A', 'D', 'F#'],
            'A_minor': ['A', 'E_high', 'A', 'C', 'E_high'],
            'E_minor': ['E_low', 'B', 'E_high', 'G', 'B', 'E_high'],
            'F_major': ['F', 'A', 'C', 'F']
        }
    
    def safe_stop(self):
        """安全停止应用程序"""
        # 在 run() 方法中会释放资源，这里只是标记
        self.is_running = False
        print("🛑 正在安全切换应用程序...")
    
    def apply_custom_css(self):
        """应用自定义CSS样式"""
        st.markdown("""
        <style>
            /* 主背景和文本颜色 */
            .stApp {
                background: linear-gradient(135deg, #0f0c1d 0%, #1a1730 50%, #0f0c1d 100%);
                color: #ffffff;
            }
            
            /* 标题样式 */
            .main-header {
                background: linear-gradient(135deg, #6a11cb, #ff0080, #00d4ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                font-size: 3.5rem !important;
                font-weight: 800 !important;
                margin-bottom: 10px !important;
                text-shadow: 0 5px 15px rgba(106, 17, 203, 0.3);
            }
            
            .sub-header {
                color: #b8b5d0;
                text-align: center;
                font-size: 1.2rem;
                margin-bottom: 30px;
            }
            
            /* 侧边栏样式 */
            section[data-testid="stSidebar"] {
                background: linear-gradient(135deg, #1a1730, #151225) !important;
                border-right: 1px solid rgba(106, 17, 203, 0.3);
            }
            
            .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6 {
                color: #ffffff !important;
            }
            
            .stSidebar p, .stSidebar label, .stSidebar span {
                color: #b8b5d0 !important;
            }
            
            /* 滑块样式 */
            .stSlider > div > div > div {
                background: linear-gradient(90deg, #6a11cb, #00d4ff) !important;
            }
            
            .stSlider > div > div > div > div {
                background: #ffffff !important;
            }
            
            /* 选择框样式 */
            .stSelectbox > div > div > div {
                background: #1a1730 !important;
                border: 1px solid #6a11cb !important;
                color: #ffffff !important;
            }
            
            /* 按钮样式 */
            .stButton > button {
                background: linear-gradient(135deg, #6a11cb, #ff0080) !important;
                color: white !important;
                border: none !important;
                border-radius: 10px !important;
                padding: 10px 20px !important;
                font-weight: bold !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3) !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(106, 17, 203, 0.5) !important;
                background: linear-gradient(135deg, #7a1bdb, #ff2090) !important;
            }
            
            .stButton > button:active {
                transform: translateY(1px) !important;
            }
            
            /* 主要按钮 - 停止/开始 */
            .primary-button > button {
                background: linear-gradient(135deg, #ff0080, #ff6b9d) !important;
            }
            
            /* 复选框样式 */
            .stCheckbox > label {
                color: #ffffff !important;
                font-weight: 500 !important;
            }
            
            .stCheckbox > div > div {
                background: #1a1730 !important;
                border: 2px solid #6a11cb !important;
            }
            
            /* 指标卡片样式 */
            [data-testid="stMetricValue"] {
                color: #00d4ff !important;
                font-size: 1.8rem !important;
                font-weight: bold !important;
            }
            
            [data-testid="stMetricLabel"] {
                color: #b8b5d0 !important;
            }
            
            /* 信息框样式 */
            .stAlert {
                background: rgba(106, 17, 203, 0.1) !important;
                border: 1px solid rgba(106, 17, 203, 0.3) !important;
                color: #ffffff !important;
                border-radius: 10px !important;
            }
            
            /* 成功消息 */
            .stSuccess {
                background: rgba(0, 212, 255, 0.1) !important;
                border: 1px solid rgba(0, 212, 255, 0.3) !important;
                color: #00d4ff !important;
            }
            
            /* 错误消息 */
            .stError {
                background: rgba(255, 0, 128, 0.1) !important;
                border: 1px solid rgba(255, 0, 128, 0.3) !important;
                color: #ff0080 !important;
            }
            
            /* 警告消息 */
            .stWarning {
                background: rgba(255, 200, 0, 0.1) !important;
                border: 1px solid rgba(255, 200, 0, 0.3) !important;
                color: #ffcc00 !important;
            }
            
            /* 信息消息 */
            .stInfo {
                background: rgba(106, 17, 203, 0.1) !important;
                border: 1px solid rgba(106, 17, 203, 0.3) !important;
                color: #b8b5d0 !important;
            }
            
            /* 分割线 */
            hr {
                border: none;
                height: 1px;
                background: linear-gradient(90deg, transparent, #6a11cb, transparent);
                margin: 20px 0;
            }
            
            /* 卡片容器 */
            .custom-card {
                background: rgba(26, 23, 48, 0.8);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(106, 17, 203, 0.3);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
                margin-bottom: 20px;
            }
            
            /* 实时视图容器 */
            .video-container {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 15px;
                border: 2px solid rgba(106, 17, 203, 0.3);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
            }
            
            /* 手部信息容器 */
            .hand-info-container {
                background: rgba(26, 23, 48, 0.9);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(0, 212, 255, 0.3);
                height: 100%;
            }
            
            /* 和弦显示容器 */
            .chord-display {
                background: linear-gradient(135deg, rgba(106, 17, 203, 0.3), rgba(0, 212, 255, 0.3));
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                margin: 20px 0;
                border: 2px solid rgba(106, 17, 203, 0.5);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            }
            
            /* 特效设置容器 */
            .effects-container {
                background: rgba(26, 23, 48, 0.9);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(255, 50, 150, 0.3);
                margin-bottom: 20px;
            }
            
            /* 响应式调整 */
            @media (max-width: 768px) {
                .main-header {
                    font-size: 2.2rem !important;
                }
                .video-container {
                    padding: 10px;
                }
            }
        </style>
        """, unsafe_allow_html=True)
    
    def setup_components(self):
        """设置各个组件"""
        try:
            self.hand_tracker = HandTracker(self.config['hand_tracking'])
            self.gesture_analyzer = GestureAnalyzer(self.config)
            self.audio_system = AudioSystem(self.config['audio'])
            # 注意：这里移除了 guitar_3d 初始化
            print("✅ 所有组件初始化成功")
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")
    
    def create_particle(self, x, y, particle_type):
        """创建粒子特效 - 增强版"""
        particle_types = {
            'C_major': {  # 红色气球特效 🎈
                'color': (255, 50, 50),
                'size_range': (15, 30),  # 增大尺寸范围
                'life_range': (40, 80),  # 增加生命周期
                'speed_x_range': (-3, 3),  # 增加速度范围
                'speed_y_range': (-4, -2),  # 向上漂浮
                'type': 'balloon',
                'count': 8,  # 每次创建的数量
                'alpha_range': (0.6, 1.0)  # 透明度范围
            },
            'G_major': {  # 青色雪花特效 ❄️
                'color': (100, 255, 255),
                'size_range': (8, 20),
                'life_range': (50, 100),
                'speed_x_range': (-2, 2),
                'speed_y_range': (1.5, 4),
                'type': 'snow',
                'count': 10,
                'alpha_range': (0.7, 1.0)
            },
            'D_major': {  # 蓝色泡泡特效 🫧
                'color': (100, 150, 255),
                'size_range': (12, 25),
                'life_range': (60, 120),
                'speed_x_range': (-2.5, 2.5),
                'speed_y_range': (-1, 1),
                'type': 'bubble',
                'count': 12,
                'alpha_range': (0.5, 0.9)
            },
            'A_minor': {  # 绿色闪烁特效 ✨
                'color': (100, 255, 100),
                'size_range': (5, 15),
                'life_range': (30, 60),
                'speed_x_range': (-4, 4),
                'speed_y_range': (-4, 4),
                'type': 'sparkle',
                'count': 15,
                'alpha_range': (0.8, 1.0)
            },
            'E_minor': {  # 黄色萤火虫特效 🪰
                'color': (255, 255, 100),
                'size_range': (6, 12),
                'life_range': (80, 160),
                'speed_x_range': (-1.5, 1.5),
                'speed_y_range': (-1, 1),
                'type': 'firefly',
                'count': 10,
                'alpha_range': (0.6, 1.0)
            },
            'F_major': {  # 紫色魔法特效 🔮
                'color': (200, 100, 255),
                'size_range': (15, 35),
                'life_range': (90, 180),
                'speed_x_range': (-1, 1),
                'speed_y_range': (-2.5, -1),
                'type': 'magic',
                'count': 8,
                'alpha_range': (0.7, 1.0)
            }
        }
        
        if particle_type in particle_types:
            config = particle_types[particle_type]
            
            # 创建多个粒子
            particles_to_create = config['count']
            for _ in range(particles_to_create):
                # 在周围随机位置创建粒子
                offset_x = random.randint(-60, 60)
                offset_y = random.randint(-60, 60)
                particle_x = x + offset_x
                particle_y = y + offset_y
                
                # 生成随机属性
                size = random.randint(config['size_range'][0], config['size_range'][1])
                life = random.randint(config['life_range'][0], config['life_range'][1])
                speed_x = random.uniform(config['speed_x_range'][0], config['speed_x_range'][1])
                speed_y = random.uniform(config['speed_y_range'][0], config['speed_y_range'][1])
                alpha = random.uniform(config['alpha_range'][0], config['alpha_range'][1])
                
                # 添加一些颜色变化
                color_variation = random.randint(-30, 30)
                color = (
                    max(0, min(255, config['color'][0] + color_variation)),
                    max(0, min(255, config['color'][1] + color_variation)),
                    max(0, min(255, config['color'][2] + color_variation))
                )
                
                self.particles.append({
                    'x': particle_x,
                    'y': particle_y,
                    'color': color,
                    'size': size,
                    'life': life,
                    'max_life': life,
                    'speed_x': speed_x,
                    'speed_y': speed_y,
                    'type': config['type'],
                    'particle_type': particle_type,
                    'alpha': alpha,
                    'rotation': random.uniform(0, 360),  # 旋转角度
                    'rotation_speed': random.uniform(-5, 5),  # 旋转速度
                    'glow_intensity': random.uniform(0.5, 1.0)  # 发光强度
                })
    
    def update_particles(self):
        """更新粒子特效 - 增强版"""
        current_time = time.time()
        
        # 根据当前和弦添加新粒子
        if (self.current_chord and self.current_chord != "none" and 
            self.current_chord != "unknown" and 
            current_time - self.last_particle_time > 0.05):  # 减少间隔时间，增加频率
            
            # 在手部位置添加粒子
            if hasattr(self, 'last_hand_positions'):
                for pos in self.last_hand_positions:
                    # 每次在手部位置创建粒子
                    self.create_particle(pos[0], pos[1], self.current_chord)
            
            self.last_particle_time = current_time
        
        # 更新现有粒子
        for particle in self.particles[:]:
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']
            particle['life'] -= 1
            
            # 更新旋转
            particle['rotation'] += particle['rotation_speed']
            
            # 根据粒子类型添加特殊效果
            if particle['type'] == 'bubble':
                particle['size'] += 0.15  # 泡泡更快变大
                particle['speed_y'] -= 0.02  # 泡泡向上加速
            elif particle['type'] == 'sparkle':
                particle['speed_x'] *= 0.97  # 闪烁粒子更慢减速
                particle['speed_y'] *= 0.97
                # 闪烁效果
                particle['alpha'] = particle['alpha'] * (0.7 + 0.3 * np.sin(current_time * 15))
            elif particle['type'] == 'firefly':
                # 萤火虫更明显的闪烁效果
                particle['size'] = particle['size'] * (0.6 + 0.5 * np.sin(current_time * 12))
                # 随机方向变化
                if random.random() < 0.05:
                    particle['speed_x'] += random.uniform(-0.3, 0.3)
                    particle['speed_y'] += random.uniform(-0.3, 0.3)
            elif particle['type'] == 'magic':
                # 魔法粒子旋转和缩放
                particle['size'] = particle['size'] * (0.9 + 0.2 * np.sin(current_time * 8))
            
            # 限制粒子数量，防止过多
            if len(self.particles) > 500:  # 最多500个粒子
                # 移除最老的粒子
                if particle['life'] < particle['max_life'] * 0.3:
                    self.particles.remove(particle)
                    continue
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw_particles(self, frame):
        """在帧上绘制粒子特效 - 增强版"""
        frame_height, frame_width = frame.shape[:2]
        
        for particle in self.particles:
            if particle['life'] > 0:
                x, y = int(particle['x']), int(particle['y'])
                size = int(particle['size'])
                color = particle['color']
                alpha = particle['life'] / particle['max_life']
                alpha *= particle['alpha']  # 应用随机alpha
                
                # 确保粒子在画面内
                if x < 0 or x >= frame_width or y < 0 or y >= frame_height:
                    continue
                
                # 根据粒子类型绘制不同形状
                if particle['type'] == 'balloon':
                    # 绘制圆形气球，带阴影效果
                    radius = max(1, int(size * alpha))
                    glow_radius = int(radius * 1.5)
                    
                    # 绘制发光效果
                    for r in range(glow_radius, 0, -1):
                        alpha_layer = alpha * (r / glow_radius) * 0.2
                        color_with_alpha = tuple(int(c * alpha_layer) for c in color)
                        cv2.circle(frame, (x, y), r, color_with_alpha, -1)
                    
                    # 绘制主气球
                    cv2.circle(frame, (x, y), radius, color, -1)
                    # 气球线
                    line_length = size // 2
                    cv2.line(frame, (x, y+radius), (x, y+radius+line_length), color, 2)
                    
                elif particle['type'] == 'snow':
                    # 绘制雪花（多个交叉的线）
                    angle = particle['rotation']
                    for i in range(6):
                        rad = np.radians(angle + i * 60)
                        x1 = int(x + np.cos(rad) * size)
                        y1 = int(y + np.sin(rad) * size)
                        cv2.line(frame, (x, y), (x1, y1), color, 2)
                    
                    # 中心点
                    cv2.circle(frame, (x, y), 2, color, -1)
                    
                elif particle['type'] == 'bubble':
                    # 绘制泡泡（圆形加高光）
                    cv2.circle(frame, (x, y), size, color, 2)
                    # 高光
                    highlight_x = x - size//3
                    highlight_y = y - size//3
                    highlight_size = size//4
                    cv2.circle(frame, (highlight_x, highlight_y), highlight_size, (255, 255, 255), -1)
                    
                elif particle['type'] == 'sparkle':
                    # 绘制闪烁星星
                    angle = particle['rotation']
                    for i in range(4):
                        rad = np.radians(angle + i * 90)
                        x1 = int(x + np.cos(rad) * size)
                        y1 = int(y + np.sin(rad) * size)
                        cv2.line(frame, (x, y), (x1, y1), color, 2)
                    
                    # 绘制对角线
                    for i in range(4):
                        rad = np.radians(angle + i * 90 + 45)
                        x1 = int(x + np.cos(rad) * size * 0.7)
                        y1 = int(y + np.sin(rad) * size * 0.7)
                        cv2.line(frame, (x, y), (x1, y1), color, 1)
                    
                elif particle['type'] == 'firefly':
                    # 绘制萤火虫（发光点）
                    glow_size = int(size * particle['glow_intensity'] * 2.5)
                    for r in range(glow_size, 0, -1):
                        alpha_layer = alpha * (r / glow_size) * 0.4
                        color_with_alpha = tuple(int(c * alpha_layer) for c in color)
                        cv2.circle(frame, (x, y), r, color_with_alpha, -1)
                    
                    # 中心亮点
                    cv2.circle(frame, (x, y), size, color, -1)
                    
                elif particle['type'] == 'magic':
                    # 绘制魔法星形
                    angle = particle['rotation']
                    points = []
                    for i in range(5):
                        outer_angle = np.radians(angle + i * 72)
                        outer_x = int(x + np.cos(outer_angle) * size)
                        outer_y = int(y + np.sin(outer_angle) * size)
                        points.append((outer_x, outer_y))
                        
                        inner_angle = np.radians(angle + i * 72 + 36)
                        inner_x = int(x + np.cos(inner_angle) * (size/2))
                        inner_y = int(y + np.sin(inner_angle) * (size/2))
                        points.append((inner_x, inner_y))
                    
                    # 绘制五角星
                    for i in range(len(points)):
                        cv2.line(frame, points[i], points[(i+1)%len(points)], color, 3)
                    
                    # 中心光晕
                    for r in range(size*2, 0, -2):
                        alpha_layer = alpha * (r / (size*2)) * 0.3
                        color_with_alpha = tuple(int(c * alpha_layer) for c in color)
                        cv2.circle(frame, (x, y), r, color_with_alpha, 1)
        
        return frame
    
    def update_strings_wave(self, chord):
        """更新吉他弦波形数据"""
        # 重置所有弦的激活状态
        for string in self.strings_data.values():
            string['active'] = False
        
        # 根据和弦激活相应的弦
        if chord in self.chord_string_mapping:
            active_strings = self.chord_string_mapping[chord]
            for string_name in active_strings:
                if string_name in self.strings_data:
                    self.strings_data[string_name]['active'] = True
        
        # 为所有弦更新波形数据
        current_time = time.time()
        for string_name, string_data in self.strings_data.items():
            wave = string_data['wave']
            
            # 限制波形长度
            if len(wave) > 100:
                wave = wave[-100:]
            
            # 生成新的波形点
            if string_data['active']:
                # 激活的弦有更大的振幅
                amplitude = 25 + 15 * np.sin(current_time * 6 + hash(string_name) % 10)
                frequency = 2.5 + 1.5 * np.sin(current_time * 2.5)
            else:
                # 未激活的弦有较小的背景波动
                amplitude = 5 + 2 * np.sin(current_time * 2 + hash(string_name) % 10)
                frequency = 0.5
            
            new_value = amplitude * np.sin(current_time * frequency)
            wave.append(new_value)
            
            # 保持波形数据
            string_data['wave'] = wave[-100:]  # 只保留最近100个点
    
    def draw_guitar_strings(self, frame_height=400, frame_width=300):
        """绘制吉他弦曲线谱 - 修复中文显示问题"""
        # 使用PIL创建图像以支持中文显示
        img = Image.new('RGB', (frame_width, frame_height), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            # 尝试加载中文字体
            font_path = None
            # 常见中文字体路径
            possible_fonts = [
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',  # Linux
                'C:/Windows/Fonts/msyh.ttc',  # Windows
                'C:/Windows/Fonts/simhei.ttf',  # Windows
                './fonts/wqy-microhei.ttc'  # 当前目录
            ]
            
            for path in possible_fonts:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if font_path:
                font = ImageFont.truetype(font_path, 14)
                small_font = ImageFont.truetype(font_path, 12)
                title_font = ImageFont.truetype(font_path, 18)
            else:
                # 如果找不到中文字体，使用默认字体（显示英文）
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                title_font = ImageFont.load_default()
                print("⚠️ 未找到中文字体，将使用默认字体")
        except Exception as e:
            print(f"⚠️ 字体加载失败: {e}")
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        
        # 弦的数量和间距
        num_strings = 6
        margin_top = 50
        margin_bottom = 50
        available_height = frame_height - margin_top - margin_bottom
        string_spacing = available_height / (num_strings - 1)
        
        # 弦名映射
        string_names = {
            'E_low': 'E低音弦',
            'A': 'A弦',
            'D': 'D弦', 
            'G': 'G弦',
            'B': 'B弦',
            'E_high': 'E高音弦'
        }
        
        # 绘制每根弦
        string_keys = list(self.strings_data.keys())
        for i, string_key in enumerate(string_keys):
            y_pos = int(margin_top + i * string_spacing)
            string_data = self.strings_data[string_key]
            color = string_data['color']
            
            # 绘制弦名（左侧）
            string_name = string_names.get(string_key, string_key)
            
            # 绘制文本背景
            text_bbox = draw.textbbox((0, 0), string_name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 绘制背景矩形
            draw.rectangle(
                [(5, y_pos - text_height//2), 
                 (5 + text_width + 10, y_pos + text_height//2)],
                fill=(40, 40, 60)
            )
            
            # 绘制弦名
            draw.text(
                (10, y_pos - text_height//2),
                string_name,
                font=font,
                fill=(255, 255, 255)
            )
            
            # 绘制基准线（弦的位置）
            line_thickness = 2 if string_data['active'] else 1
            line_color = color if string_data['active'] else (color[0]//3, color[1]//3, color[2]//3)
            draw.line(
                [(80, y_pos), (frame_width - 20, y_pos)],
                fill=line_color,
                width=line_thickness
            )
            
            # 绘制波形
            wave = string_data['wave']
            if len(wave) > 1:
                points = []
                for j, value in enumerate(wave):
                    x = frame_width - 20 - (len(wave) - j) * 2
                    if x < 80:
                        continue
                    y = y_pos + int(value * 0.5)  # 缩放波形
                    points.append((x, y))
                
                if len(points) > 1:
                    # 绘制波形线
                    for j in range(len(points) - 1):
                        draw.line(
                            [points[j], points[j+1]],
                            fill=color,
                            width=1
                        )
                    
                    # 绘制波形点（仅激活的弦）
                    if string_data['active']:
                        for point in points[-10:]:  # 只绘制最近的点
                            draw.ellipse(
                                [point[0]-2, point[1]-2, point[0]+2, point[1]+2],
                                fill=color,
                                outline=color
                            )
            
            # 绘制弦头（右侧）
            draw.ellipse(
                [(frame_width - 25, y_pos - 5), (frame_width - 15, y_pos + 5)],
                fill=color,
                outline=color
            )
        
        # 添加标题
        title = "吉他弦曲线谱"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((frame_width - title_width) // 2, 20),
            title,
            font=title_font,
            fill=(255, 255, 255)
        )
        
        # 添加图例说明
        legend_text = "● 激活 | ○ 静音"
        legend_bbox = draw.textbbox((0, 0), legend_text, font=small_font)
        legend_width = legend_bbox[2] - legend_bbox[0]
        draw.text(
            ((frame_width - legend_width) // 2, frame_height - 30),
            legend_text,
            font=small_font,
            fill=(200, 200, 200)
        )
        
        # 转换回numpy数组
        strings_canvas = np.array(img)
        
        return strings_canvas
    
    def get_unique_key(self, base_name: str) -> str:
        """生成唯一的元素key"""
        self.button_counter += 1
        return f"{base_name}_{self.button_counter}"
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """处理单帧图像"""
        # 手部追踪
        processed_frame, hand_data = self.hand_tracker.process_frame(frame)
        
        # 保存手部位置用于粒子特效
        self.last_hand_positions = []
        for hand in hand_data:
            if 'landmarks' in hand and hand['landmarks']:
                # 使用手掌中心作为粒子发射位置
                landmarks = hand['landmarks']
                if landmarks and len(landmarks) > 0:
                    center_x = int(np.mean([lm[0] for lm in landmarks]))
                    center_y = int(np.mean([lm[1] for lm in landmarks]))
                    self.last_hand_positions.append((center_x, center_y))
        
        # 手势分析
        analyzed_data = []
        current_chord = "none"
        
        for hand in hand_data:
            analysis = self.gesture_analyzer.analyze_hand_position(hand, frame.shape)
            analyzed_data.append(analysis)
            
            if analysis['detected'] and analysis['gesture'] != "unknown":
                current_chord = analysis['gesture']
                # 更新调试信息
                features = analysis.get('hand_features', {})
                extended_count = features.get('extended_count', 0)
                hand_position = self.gesture_analyzer.get_hand_position(analysis['bounding_box'])
                self.debug_info = f"识别成功: {current_chord} | 伸直手指: {extended_count}个 | 位置: {hand_position}"
        
        # 更新和弦状态
        if current_chord != self.current_chord and current_chord != "unknown":
            self.on_chord_change(current_chord)
        
        # 检测扫弦动作
        if self.prev_hand_data and analyzed_data and len(analyzed_data) > 0:
            strum_direction = self.gesture_analyzer.calculate_strumming_direction(
                self.prev_hand_data[0], analyzed_data[0]
            )
            if strum_direction != "none":
                self.on_strum_detected(strum_direction)
        
        # 更新粒子特效
        self.update_particles()
        
        # 更新吉他弦波形
        self.update_strings_wave(current_chord)
        
        self.prev_hand_data = analyzed_data
        self.current_chord = current_chord
        
        # 应用粒子特效到处理后的帧
        if processed_frame is not None:
            processed_frame = self.draw_particles(processed_frame)
        
        return {
            'processed_frame': processed_frame,
            'hand_data': analyzed_data,
            'current_chord': current_chord,
            'strings_canvas': self.draw_guitar_strings()
        }
    
    def on_chord_change(self, new_chord: str):
        """处理和弦变化"""
        print(f"🎵 检测到和弦变化: {new_chord}")
        
        self.chord_history.append({
            'chord': new_chord,
            'time': time.time()
        })
        
        if len(self.chord_history) > 10:
            self.chord_history.pop(0)
        
        if new_chord != "none" and new_chord != "unknown":
            self.audio_system.play_chord(new_chord)
    
    def on_strum_detected(self, direction: str):
        """处理扫弦检测"""
        print(f"🎸 检测到扫弦: {direction}")
        self.audio_system.play_effect("pick_noise", 0.3)
    
    def update_fps(self):
        """更新FPS计算"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def render_chord_display(self, chord: str):
        """渲染和弦显示"""
        if chord and chord != "none" and chord != "unknown":
            chord_colors = {
                'C_major': '#FF6B6B',
                'G_major': '#4ECDC4', 
                'D_major': '#45B7D1',
                'A_minor': '#96CEB4',
                'E_minor': '#FFEAA7',
                'F_major': '#DDA0DD'
            }
            
            color = chord_colors.get(chord, '#FF6B6B')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, {color}, #2C3E50); 
                        border-radius: 15px; margin: 20px 0; box-shadow: 0 8px 25px rgba(0,0,0,0.3);">
                <h1 style="color: white; margin: 0; font-size: 3rem;">🎵 {chord}</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">当前检测到的和弦</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea, #764ba2); 
                        border-radius: 15px; margin: 20px 0;">
                <h2 style="color: white; margin: 0;">🎸 等待检测和弦...</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">请做出和弦手势</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_chord_guide(self):
        """渲染和弦手势指南"""
        st.subheader("🎯 和弦手势指南 - 手指数量+位置")
        
        # 基于手指数量和位置的手势设计
        chords_guide = {
            'C_major': {
                'description': "✌️ 两指伸直 + 手部抬高",
                'instruction': "伸直任意两指，将手放在画面上半部分",
                'fingers': "2指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#FF6B6B',
                'icon': '✌️'
            },
            'G_major': {
                'description': "✌️ 两指伸直 + 手部放低", 
                'instruction': "伸直任意两指，将手放在画面下半部分",
                'fingers': "2指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#4ECDC4',
                'icon': '✌️'
            },
            'D_major': {
                'description': "🤟 三指伸直 + 手部抬高",
                'instruction': "伸直任意三指，将手放在画面上半部分",
                'fingers': "3指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#45B7D1',
                'icon': '🤟'
            },
            'A_minor': {
                'description': "🤟 三指伸直 + 手部放低",
                'instruction': "伸直任意三指，将手放在画面下半部分",
                'fingers': "3指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#96CEB4',
                'icon': '🤟'
            },
            'E_minor': {
                'description': "🖖 四指伸直 + 手部抬高",
                'instruction': "伸直任意四指，将手放在画面上半部分",
                'fingers': "4指伸直",
                'position': "较高位置（画面上半部）",
                'color': '#FFEAA7',
                'icon': '🖖'
            },
            'F_major': {
                'description': "🖖 四指伸直 + 手部放低",
                'instruction': "伸直任意四指，将手放在画面下半部分",
                'fingers': "4指伸直",
                'position': "较低位置（画面下半部）",
                'color': '#DDA0DD',
                'icon': '🖖'
            }
        }
        
        # 按列显示
        cols = st.columns(2)
        for i, (chord, info) in enumerate(chords_guide.items()):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="padding: 15px; background: {info['color']}20; border-radius: 10px; border-left: 4px solid {info['color']}; margin: 5px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 1.5em; margin-right: 10px;">{info['icon']}</span>
                            <h4 style="margin: 0; color: {info['color']};">{chord}</h4>
                        </div>
                        <p style="margin: 5px 0 0 0; font-size: 0.9em; font-weight: bold;">{info['description']}</p>
                        <p style="margin: 3px 0 0 0; font-size: 0.8em; color: #666;">{info['instruction']}</p>
                        <p style="margin: 2px 0 0 0; font-size: 0.8em; color: #888;">
                            🎯 {info['fingers']} | 📍 {info['position']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 位置示意图
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0; color: #495057;">📍 位置示意图：</h4>
            <div style="text-align: center; margin: 10px 0;">
                <div style="background: #e74c3c; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔺 较高位置 - 手在画面上半部（屏幕上半部分）
                </div>
                <div style="background: #f39c12; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔸 中间位置 - 手在画面中部
                </div>
                <div style="background: #27ae60; color: white; padding: 10px; margin: 5px; border-radius: 5px;">
                    🔻 较低位置 - 手在画面下半部（屏幕下半部分）
                </div>
            </div>
            <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #666;">
                💡 <strong>重要提示</strong>: 确保手指完全伸直，手部位置明显区分高低
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 调试提示
        st.markdown("""
        <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0; color: #1976d2;">🔧 调试提示：</h4>
            <ul style="margin: 5px 0 0 0;">
                <li>查看下方<strong>识别信息</strong>了解当前检测状态</li>
                <li>确保手指<strong>完全伸直</strong>，不要半弯曲</li>
                <li>手部位置要<strong>明显区分高低</strong></li>
                <li>保持手势<strong>稳定1-2秒</strong>让系统识别</li>
                <li>查看控制台获取<strong>详细调试信息</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("⚙️ 设置")
            
            st.markdown("---")           
            # 音频设置
            volume = st.slider("音量", 0.0, 1.0, 0.7, key="volume")
            self.audio_system.set_volume(volume)
            
            # 识别设置
            st.header("🎯 识别设置")
            show_detailed_info = st.checkbox("显示详细识别信息", value=True)
            
            # 特效设置
            st.header("🎨 特效设置")
            particle_intensity = st.slider("粒子特效强度", 1, 10, 5, key="particle_intensity")
            self.particle_intensity = particle_intensity / 5.0  # 转换为倍数
            
            st.header("🎵 快速测试")
            
            # 和弦测试按钮
            test_cols = st.columns(3)
            with test_cols[0]:
                if st.button("C", width='stretch'):
                    self.audio_system.play_chord("C_major")
                    st.success("播放 C大调")
            with test_cols[1]:
                if st.button("G", width='stretch'):
                    self.audio_system.play_chord("G_major")
                    st.success("播放 G大调")
            with test_cols[2]:
                if st.button("D", width='stretch'):
                    self.audio_system.play_chord("D_major")
                    st.success("播放 D大调")
            
            test_cols2 = st.columns(3)
            with test_cols2[0]:
                if st.button("Am", width='stretch'):
                    self.audio_system.play_chord("A_minor")
                    st.success("播放 A小调")
            with test_cols2[1]:
                if st.button("Em", width='stretch'):
                    self.audio_system.play_chord("E_minor")
                    st.success("播放 E小调")
            with test_cols2[2]:
                if st.button("F", width='stretch'):
                    self.audio_system.play_chord("F_major")
                    st.success("播放 F大调")
            
            # 音频控制
            st.header("🔊 音频控制")
            audio_cols = st.columns(2)
            with audio_cols[0]:
                if st.button("测试单音", width='stretch'):
                    self.audio_system.play_note("A")
                    st.info("播放 A音")
            with audio_cols[1]:
                if st.button("停止所有", width='stretch'):
                    self.audio_system.stop_all()
                    st.info("停止所有音频")
            
            return {
                'volume': volume,
                'show_detailed_info': show_detailed_info,
                'particle_intensity': particle_intensity
            }
    
    def run(self):
        """运行主应用程序"""
        self.apply_custom_css()
        st.markdown("""
<div style="text-align: center; margin: 15px 0;">
    <h1 style="
        background: linear-gradient(135deg, #6a11cb, #ff0080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        padding: 8px 0;
        text-shadow: 0 3px 10px rgba(106, 17, 203, 0.3);
    ">
    🎸 Air Guitar Advanced - 智能空气吉他
    </h1>
</div>
""", unsafe_allow_html=True)
        
        # 渲染侧边栏
        settings = self.render_sidebar()
        
        # 初始化摄像头
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ 无法访问摄像头，请检查摄像头连接")
            st.info("💡 请确保：")
            st.info("1. 摄像头已连接且未被其他程序占用")
            st.info("2. 浏览器已获得摄像头权限")
            st.info("3. 摄像头驱动程序正常")
            return
        
        st.success("✅ 摄像头初始化成功")
        
        # 创建占位符
        frame_placeholder = st.empty()
        status_placeholder = st.empty()
        chord_placeholder = st.empty()
        debug_placeholder = st.empty()
        
        # 控制按钮
        st.markdown("---")
        control_col1, control_col2, control_col3 = st.columns(3)
        with control_col1:
            stop_button = st.button("🛑 停止应用", key=self.get_unique_key("stop"), width='stretch', type="primary")
        with control_col2:
            test_all_button = st.button("🎵 测试所有和弦", key=self.get_unique_key("test_all"), width='stretch')
        with control_col3:
            if st.button("🔄 重新开始", key=self.get_unique_key("restart"), width='stretch'):
                st.rerun()
        
        # 显示和弦指南
        self.render_chord_guide()
        
        if test_all_button:
            # 测试所有和弦
            st.info("🎶 正在播放所有和弦...")
            for chord in ["C_major", "G_major", "D_major", "A_minor", "E_minor", "F_major"]:
                self.audio_system.play_chord(chord)
                time.sleep(0.8)
        
        self.is_running = True
        
        try:
            while self.is_running and cap.isOpened():
                if stop_button:
                    self.is_running = False
                    st.info("⏹️ 应用正在停止...")
                    break
                
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ 无法读取摄像头帧")
                    break
                
                # 处理帧
                results = self.process_frame(frame)
                
                # 更新FPS
                self.update_fps()
                
                # 更新UI
                with frame_placeholder.container():
                    # 创建三列，宽度比例为1:2:1
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.subheader("👋 手部信息")
                        if results['hand_data'] and len(results['hand_data']) > 0:
                            hand = results['hand_data'][0]  # 只取第一个手部信息
                            
                            if hand.get('detected', False):
                                with st.container():
                                    st.write(f"**手**: {hand.get('hand_type', 'unknown')}")
                                    st.write(f"**和弦**: {hand.get('gesture', 'unknown')}")
                                    features = hand.get('hand_features', {})
                                    extended_count = features.get('extended_count', 0)
                                    st.write(f"**伸直手指**: {extended_count}个")
                                    
                                    # 显示手指状态
                                    finger_states = features.get('finger_states', {})
                                    if finger_states:
                                        st.write("**手指状态**:")
                                        finger_names = {
                                            'thumb': '大拇指',
                                            'index': '食指',
                                            'middle': '中指',
                                            'ring': '无名指',
                                            'pinky': '小指'
                                        }
                                        for finger, state in finger_states.items():
                                            status = "🟢 伸直" if state else "🔴 弯曲"
                                            display_name = finger_names.get(finger, finger)
                                            st.write(f"  {display_name}: {status}")
                            else:
                                st.warning("👋 手部未正确检测，请调整手势")
                                st.info("💡 提示：确保手指完全伸直，手部位置明显")
                        else:
                            st.warning("👋 未检测到手部，请将手放在摄像头前")
                           
                    
                    with col2:
                        st.subheader("📷 实时视图")
                        if results['processed_frame'] is not None:
                            # 显示带粒子特效的实时视图
                            st.image(results['processed_frame'], channels="BGR", width='stretch')
                    
                    with col3:
                        st.subheader("🎸 吉他弦曲线谱")
                        if 'strings_canvas' in results and results['strings_canvas'] is not None:
                            # 显示吉他弦曲线谱
                            st.image(results['strings_canvas'], channels="RGB", width='stretch')
                        
                        # 特效说明
                        with st.expander("🎨 增强特效说明"):
                            st.markdown("""
                            **六种弦对应的粒子特效（增强版）：**
                            - 🎈 **C弦**: 气球特效 - 大量气球向上漂浮
                            - ❄️ **G弦**: 雪花特效 - 雪花状粒子缓缓下落  
                            - 🫧 **D弦**: 泡泡特效 - 泡泡慢慢变大并上升
                            - ✨**A弦**: 闪烁特效 - 快速闪烁的星星状粒子
                            - 🪰 **E弦**: 萤火虫特效 - 发光点随机游动
                            - 🔮 **F弦**: 紫色魔法特效 - 旋转的五角星魔法效果
                            
                            **吉他弦说明：**
                            - 六根不同颜色的吉他弦
                            - 每根弦都有动态波形
                            - 和弦变化时对应弦会产生强烈波动
                            """)
                
                # 更新状态信息
                with status_placeholder.container():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 FPS", f"{self.fps:.1f}")
                    with col2:
                        st.metric("👋 检测手部", len(results['hand_data']))
                    with col3:
                        if results['current_chord'] and results['current_chord'] != "none":
                            st.metric("🎵 当前和弦", results['current_chord'])
                        else:
                            st.metric("🎵 当前和弦", "等待中")
                
                # 更新和弦显示
                with chord_placeholder.container():
                    self.render_chord_display(results['current_chord'])
                
                # 更新调试信息
                with debug_placeholder.container():
                    if self.debug_info:
                        st.info(f"**识别信息**: {self.debug_info}")
                    elif results['hand_data'] and results['hand_data'][0]['detected']:
                        hand = results['hand_data'][0]
                        features = hand.get('hand_features', {})
                        extended_count = features.get('extended_count', 0)
                        st.info(f"**检测状态**: 检测到手部，伸直{extended_count}个手指")
                    else:
                        st.info("**检测状态**: 等待手部检测...")
                
                # 添加小延迟以控制帧率
                time.sleep(0.03)
        
        except Exception as e:
            st.error(f"❌ 发生错误: {str(e)}")
            st.info("请检查控制台获取详细错误信息")
        
        finally:
            # 清理资源
            if cap.isOpened():
                cap.release()
                print("✅ 摄像头已释放")
            if hasattr(self, 'hand_tracker'):
                self.hand_tracker.release()
                print("✅ 手部追踪器已释放")
            if hasattr(self, 'audio_system'):
                self.audio_system.stop_all()
                print("✅ 音频系统已停止")
            
            st.success("✅ 应用已安全停止")
            st.info("🔄 如需重新启动，请刷新页面")

def main():
    """主函数"""
    try:
        app = AirGuitarApp()
        app.run()
    except Exception as e:
        st.error(f"❌ 应用启动失败: {str(e)}")
        st.info("""
        **可能的原因和解决方案：**
        1. **摄像头问题** - 检查摄像头连接和权限
        2. **依赖包缺失** - 运行 `pip install -r requirements.txt`
        3. **音频设备问题** - 检查系统音频设置
        4. **资源冲突** - 关闭其他可能占用摄像头的程序
        """)

if __name__ == "__main__":
    main()