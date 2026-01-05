import streamlit as st
import streamlit.components.v1 as components
import cv2
import pygame
import numpy as np
import time
import sys
import os
from typing import Dict, Any
from collections import deque


# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hand_tracker import HandTracker
from gesture_analyzer import GestureAnalyzer
from audio_system import AudioSystem
import utils

# 在 imports 区加入（在现有 import 之后）
try:
    from generate_guitar_samples import OUTPUT_DIR, generate_all, generate_sample_chord
except Exception:
    OUTPUT_DIR = os.path.join('assets', 'guitar_samples', 'single_notes')


    def generate_all():
        raise RuntimeError("generate_guitar_samples unavailable")


    def generate_sample_chord():
        pass


class AirGuitarApp:
    """空气吉他主应用程序"""

    def __init__(self):
        self.config = utils.load_config()
        self.setup_components()

        # 状态变量
        self.is_running = False
        self.is_playing = False
        self.recognition_enabled = True
        self.current_chord = "none"
        self.prev_hand_data = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.button_counter = 0
        self.chord_history = []
        self.debug_info = ""
        self.current_string = None
        self.current_fret = None
        self.last_played_mapping = (None, None)
        self.should_navigate = False
        self.target_page = None

        # 历史平滑缓存：每只手保留最近 N 帧的 finger_states 用于去抖
        self._finger_history = {
            'left': deque(maxlen=5),
            'right': deque(maxlen=5)
        }

    def navigate_to(self, target_page):
        """导航到其他页面"""
        self.should_navigate = True
        self.target_page = target_page
        self.is_running = False  # 停止当前循环

    def safe_stop(self):
        """安全停止应用程序"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            print("✅ 摄像头已释放")
        if hasattr(self, 'hand_tracker'):
            self.hand_tracker.release()
            print("✅ 手部追踪器已释放")
        if hasattr(self, 'audio_system'):
            self.audio_system.stop_all()
            print("✅ 音频系统已停止")

    def setup_components(self):
        """设置各个组件"""
        try:
            self.hand_tracker = HandTracker(self.config['hand_tracking'])
            self.gesture_analyzer = GestureAnalyzer(self.config)
            self.audio_system = AudioSystem(self.config['audio'])
            self.guitar_3d = None
            print("✅ 所有组件初始化成功")
        except Exception as e:
            print(f"❌ 组件初始化失败: {e}")

    def get_unique_key(self, base_name: str) -> str:
        """生成唯一的元素key"""
        self.button_counter += 1
        return f"{base_name}_{self.button_counter}"

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

            /* 侧边栏顶部切换按钮样式（新增） */
            .sidebar-top-btn > button {
                height: 60px !important;
                font-size: 1.1rem !important;
                margin-bottom: 10px !important;
                background: linear-gradient(135deg, #00d4ff, #6a11cb) !important;
            }

            .sidebar-top-btn > button:hover {
                border-color: #ff0080 !important;
                transform: translateY(-3px) !important;
            }

            /* 响应式调整 */
            @media (max-width: 768px) {
                .main-header {
                    font-size: 2.2rem !important;
                }
                .video-container {
                    padding: 10px;
                }
                .sidebar-top-btn > button {
                    height: 50px !important;
                    font-size: 1rem !important;
                }
            }
        </style>
        """, unsafe_allow_html=True)

    # ---------------------- 新增：侧边栏顶部网页切换功能 ----------------------
    def add_sidebar_top_navigation(self):
        """在侧边栏最上方添加网页切换按钮"""
        with st.sidebar:
            st.markdown("### 📱 页面切换")
            st.markdown("---")
            st.caption("若需在不同界面间切换，请使用统一入口 unified_app.py（侧边栏选择）。")

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """处理单帧图像（增加手型规范化、帧级手指去抖与左右手去重）"""
        # 手部追踪
        processed_frame, hand_data = self.hand_tracker.process_frame(frame)

        analyzed_data = []
        current_chord = "none"

        for hand in hand_data:
            # 确保手型字段规范化为 'left' / 'right'
            hand_type_norm = self._normalize_hand_type(hand)
            try:
                analysis = self.gesture_analyzer.analyze_hand_position(hand, frame.shape)
            except Exception:
                analysis = {}
            # 手势（张开/握拳）
            hand_gesture = self.hand_tracker.get_hand_gesture(hand)
            analysis['hand_gesture'] = hand_gesture

            # 标注并统一 hand_type 字段（分析结果中）
            analysis['hand_type'] = hand_type_norm

            # 获取并平滑 finger_states（若有），并更新 extended_count
            features = analysis.get('hand_features', {}) or {}
            raw_states = features.get('finger_states', {}) or {}
            smoothed = self._smooth_finger_states(hand_type_norm, raw_states)
            features['finger_states'] = smoothed
            features['extended_count'] = sum(1 for v in smoothed.values() if v)
            features['extended_count_no_thumb'] = features.get('extended_count_no_thumb', features['extended_count'] - (1 if smoothed.get('thumb') else 0))
            analysis['hand_features'] = features

            # 额外映射：根据左右手确定弦或品，并记录详细调试信息
            try:
                if hand_type_norm == 'left':
                    s = self.gesture_analyzer.map_left_hand_to_string(analysis.get('hand_features', {}))
                    analysis['string'] = s
                    print(f"DEBUG: 左手检测 -> string={s}, features={analysis.get('hand_features', {})}")
                elif hand_type_norm == 'right':
                    f = self.gesture_analyzer.determine_fret_from_right_hand(analysis.get('hand_features', {}), hand.get('landmarks', []))
                    analysis['fret'] = f
                    try:
                        print(f"DEBUG_RIGHT_MAP: fret={f} extended_count={analysis.get('hand_features', {}).get('extended_count')} features={analysis.get('hand_features', {})}")
                    except Exception:
                        print(f"DEBUG: 右手检测 -> fret={f}, features={analysis.get('hand_features', {})}")
                else:
                    print(f"DEBUG: 未知手型字段，原始手信息: {hand}")
            except Exception as e:
                print(f"DEBUG: 映射错误: {e}")

            # 保证 detected 字段存在
            if 'detected' not in analysis:
                analysis['detected'] = bool(analysis.get('hand_features'))

            analyzed_data.append(analysis)

            # 当识别被启用时进行和弦识别并更新调试信息（保留原有逻辑）
            if self.recognition_enabled and analysis.get('detected'):
                s = analysis.get('string', None)
                f = analysis.get('fret', None)
                extended_count = analysis.get('hand_features', {}).get('extended_count', 0)
                if s is not None or f is not None:
                    s_disp = s if s is not None else '-'
                    f_disp = f if f is not None else '-'
                    self.debug_info = f"映射检测: 弦 {s_disp} | 品 {f_disp} | 伸直手指: {extended_count}个"
                else:
                    if analysis.get('gesture', 'unknown') != 'unknown':
                        self.debug_info = f"(旧)识别成功: {analysis.get('gesture')} | 伸直手指: {extended_count}个"
            else:
                if analysis.get('detected') and hand_gesture == 'fist':
                    if getattr(self, 'is_playing', False):
                        try:
                            self.audio_system.stop_all()
                        except Exception:
                            pass
                        self.is_playing = False
                        self.debug_info = "手势: 握拳 - 停止播放，和弦识别已禁用"
                    else:
                        self.debug_info = "手势: 握拳 - 和弦识别已禁用"

        # 去重：同一侧可能出现多条记录（来自 Tracker 抖动），保留伸直手指数更多的一条
        deduped = {}
        for a in analyzed_data:
            ht = (a.get('hand_type') or '').lower()
            if not ht:
                continue
            cur_count = a.get('hand_features', {}).get('extended_count', 0)
            if ht not in deduped or cur_count > deduped[ht].get('hand_features', {}).get('extended_count', 0):
                deduped[ht] = a
        # 保留顺序：left then right if存在
        final_list = []
        if 'left' in deduped:
            final_list.append(deduped['left'])
        if 'right' in deduped:
            final_list.append(deduped['right'])

        analyzed_data = final_list

        # 以下逻辑保持：更新 prev_hand_data、current_string/current_fret、扫弦触发等
        try:
            if self.prev_hand_data and analyzed_data:
                prev_map = {h.get('hand_type', '').lower(): h for h in self.prev_hand_data}
                cur_map = {h.get('hand_type', '').lower(): h for h in analyzed_data}
                target = None
                if 'right' in prev_map and 'right' in cur_map:
                    target = ('right', prev_map['right'], cur_map['right'])
                elif 'left' in prev_map and 'left' in cur_map:
                    target = ('left', prev_map['left'], cur_map['left'])
                if target is not None:
                    _, prev_h, cur_h = target
                    strum_direction = self.gesture_analyzer.calculate_strumming_direction(prev_h, cur_h)
                    if strum_direction != "none":
                        self.on_strum_detected(strum_direction)
        except Exception as e:
            print(f"DEBUG: strum detection error: {e}")

        self.prev_hand_data = analyzed_data
        self.current_chord = current_chord

        # 更新当前弦/品（仅在检测到新映射时更新）
        for h in analyzed_data:
            htype = str(h.get('hand_type', '')).lower()
            if htype.startswith('l'):
                if 'string' in h:
                    self.current_string = h['string']
            elif htype.startswith('r'):
                if 'fret' in h:
                    self.current_fret = h['fret']
                else:
                    self.current_fret = 0

        found_right = any(str(h.get('hand_type', '')).lower().startswith('r') for h in analyzed_data)
        if not found_right:
            self.current_fret = 0
        found_left = any(str(h.get('hand_type', '')).lower().startswith('l') for h in analyzed_data)
        if not found_left:
            self.current_string = 0

        # 变化时播放一次预览
        try:
            mapping = (self.current_string, self.current_fret)
            if mapping != self.last_played_mapping and mapping[0] and mapping[1] is not None:
                if mapping[0] != 0 and mapping[1] >= 0:
                    try:
                        self.audio_system.play_string_fret(mapping[0], mapping[1], volume=self.audio_system.get_volume())
                    except Exception:
                        pass
                self.last_played_mapping = mapping
        except Exception:
            pass

        return {
            'processed_frame': processed_frame,
            'hand_data': analyzed_data,
            'current_chord': current_chord
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

        # 原和弦播放逻辑已弃用：应用改为基于 string/fret 的单音播放
        # 仅记录历史以便调试与回放需求
        if new_chord != "none" and new_chord != "unknown":
            self.chord_history.append({'chord': new_chord, 'time': time.time()})

    def on_strum_detected(self, direction: str):
        """处理扫弦检测"""
        print(f"🎸 检测到扫弦: {direction}")
        self.audio_system.play_effect("pick_noise", 0.3)
        # 若同时有当前弦与品的信息，则播放对应单音样本
        try:
            s = getattr(self, 'current_string', None)
            f = getattr(self, 'current_fret', None)
            print(f"DEBUG: on_strum_detected current_string={s}, current_fret={f}")
            if s is not None and f is not None:
                # 打印样本是否存在
                key = f"string{s}_fret{f}"
                exists = key in self.audio_system.samples
                print(f"DEBUG: sample {key} exists={exists}")
                if exists:
                    self.audio_system.play_string_fret(s, f, volume=self.audio_system.get_volume())
                else:
                    print(f"DEBUG: 样本未找到: {key}")
        except Exception:
            pass

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
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)

        if getattr(self, 'current_string', None) is not None or getattr(self, 'current_fret', None) is not None:
            s = self.current_string if self.current_string is not None else '-'
            f = self.current_fret if self.current_fret is not None else '-'

            st.markdown(f"""
            <div style="text-align: center; padding: 20px;">
                <h2 style="background: linear-gradient(90deg, #6a11cb, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">🎯 当前映射</h2>
                <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 15px;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.9rem; color: #b8b5d0; margin-bottom: 5px;">弦</div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #ff0080;">{s}</div>
                    </div>
                    <div style="font-size: 2rem; color: #00d4ff;">|</div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.9rem; color: #b8b5d0; margin-bottom: 5px;">品</div>
                        <div style="font-size: 2.5rem, font-weight: bold; color: #00d4ff;">{f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #ff0080; margin: 0;">等待弦/品映射...</h3>
                <p style="color: #b8b5d0; margin: 6px 0 0 0;">请展示左手弦位与右手品位</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def render_chord_guide(self):
        """渲染手势指南（仅基于伸直手指数）"""
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)

        st.markdown("""
        <h3 style="color: #00d4ff !important; border-bottom: 2px solid #6a11cb; padding-bottom: 8px;">
            🎯 手势指南 - 基于伸直手指数量
        </h3>
        """, unsafe_allow_html=True)
        chords_guide = {
            '2指': {'description': '伸直任意两指', 'fingers': '2指伸直', 'icon': '✌️', 'color': '#6a11cb'},
            '3指': {'description': '伸直任意三指', 'fingers': '3指伸直', 'icon': '🤟', 'color': '#00d4ff'},
            '4指': {'description': '伸直任意四指', 'fingers': '4指伸直', 'icon': '🖖', 'color': '#ff0080'}
        }
        cols = st.columns(3)
        for i, (k, info) in enumerate(chords_guide.items()):
            with cols[i]:
                st.markdown(f"""
                <div style="padding: 15px; background: rgba({int(info['color'][1:3], 16)}, {int(info['color'][3:5], 16)}, {int(info['color'][5:7], 16)}, 0.1); 
                            border: 1px solid {info['color']}; border-radius: 10px; margin: 6px 0; text-align: center;">
                    <div style="font-size: 2em; margin-bottom: 8px;">{info['icon']}</div>
                    <h4 style="color: {info['color']}; margin: 5px 0;">{k}</h4>
                    <p style="color: #b8b5d0; margin:0; font-size: 0.9rem;">{info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background: rgba(0, 212, 255, 0.1); padding: 12px; border-radius: 8px; margin: 15px 0 0 0; border: 1px solid #00d4ff;">
            <p style="color: #ffffff; margin: 0; font-weight: 500;">
                💡 <strong>提示</strong>: 仅使用伸直手指数量判断手势；位置不再作为判定依据。
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def render_sidebar(self):
        """渲染侧边栏（原有侧边栏内容）"""
        with st.sidebar:
            # 原有版本切换（保留，作为冗余备份）
            #st.markdown('<h3 style="color: #9ad3ff !important; margin-bottom: 12px;">🔄 版本切换（备份）</h3>',
                        #unsafe_allow_html=True)

            nav_col1, nav_col2 = st.columns(2)
            # with nav_col1:
            #     if st.button("🏠 返回主页", key="nav_home", use_container_width=True):
            #         # 安全停止当前应用
            #         self.safe_stop()
            #         # 停止Streamlit当前会话
            #         st.stop()  # 这将停止当前脚本执行
            #         # 启动主页
            #         os.system("streamlit run home_page.py")
            #
            # with nav_col2:
            #     if st.button("🎯 小白版", key="nav_novice", use_container_width=True):
            #         # 安全停止当前应用
            #         self.safe_stop()
            #         # 停止Streamlit当前会话
            #         st.stop()  # 这将停止当前脚本执行
            #         # 启动小白版
            #         os.system("streamlit run main_app1.py")

            st.markdown("---")
            # 音频设置（只保留音量大小）
            st.markdown('<h3 style="color: #ff0080 !important; margin-bottom: 12px;">🎵 音频设置</h3>',
                        unsafe_allow_html=True)
            st.markdown('<p style="color: #ffffff; margin-bottom: 8px;">音量大小</p>', unsafe_allow_html=True)
            volume = st.slider("音量", 0.0, 1.0, self.config['audio'].get('volume', 0.7), key="volume",
                               help="调整音频播放的音量大小", label_visibility="hidden")
            try:
                self.audio_system.set_volume(volume)
            except Exception:
                pass
            st.markdown("---")

            # 识别设置（保留）
            st.markdown('<h3 style="color: #00d4ff !important; margin-bottom: 15px;">🎯 识别设置</h3>',
                        unsafe_allow_html=True)
            show_detailed_info = st.checkbox("显示详细识别信息", value=True, help="显示手势识别的详细信息")
            show_opencv_debug = st.checkbox("本地调试窗口 (OpenCV)", value=False, help="在本地打开OpenCV调试窗口")

            st.markdown("---")

            # 快速测试（保留）
            st.markdown('<h3 style="color: #ff0080 !important; margin-bottom: 15px;">🎵 快速测试</h3>',
                        unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<p style="color: #ffffff; font-size: 0.9rem; margin-bottom: 5px;">选择弦 (1-6)</p>',
                            unsafe_allow_html=True)
                string_sel = st.selectbox("弦", [1, 2, 3, 4, 5, 6], index=0, help="选择要测试的吉他弦",
                                          label_visibility="hidden")
            with col2:
                st.markdown('<p style="color: #ffffff; font-size: 0.9rem; margin-bottom: 5px;">选择品 (0-10)</p>',
                            unsafe_allow_html=True)
                fret_sel = st.selectbox("品位", list(range(0, 11)), index=0, help="选择要测试的品位",
                                        label_visibility="hidden")

            if st.button("🎶 播放所选音", use_container_width=True):
                try:
                    self.audio_system.play_string_fret(string_sel, fret_sel, volume=self.audio_system.get_volume())
                    st.success(f"✅ 播放 string{string_sel}_fret{fret_sel}")
                except Exception as e:
                    st.error(f"❌ 播放失败: {e}")

            st.markdown("---")

            # 音频控制（保留基础操作）
            audio_cols = st.columns(2)
            with audio_cols[0]:
                if st.button("🎵 测试单音", use_container_width=True):
                    self.audio_system.play_note("A")
                    st.info("ℹ️ 播放 A音")
            with audio_cols[1]:
                if st.button("⏹️ 停止所有", use_container_width=True):
                    self.audio_system.stop_all()
                    st.info("ℹ️ 停止所有音频")

            # 特效选择
            st.markdown('---')
            st.markdown('<h3 style="color: #9ad3ff !important; margin-bottom: 12px;">✨ 特效设置</h3>',
                        unsafe_allow_html=True)
            effect_type = st.selectbox("选择背景特效", ["particles", "snow", "balloons", "none"], index=0,
                                       format_func=lambda x:
                                       {"particles": "粒子", "snow": "雪花", "balloons": "气球", "none": "无"}[x],
                                       help="选择右侧背景特效", label_visibility="visible")
            st.markdown('')
            return {
                'volume': volume,
                'show_detailed_info': show_detailed_info,
                'show_opencv_debug': show_opencv_debug,
                'effect_type': effect_type
            }

    def run(self):
        """运行主应用程序"""
        # 应用自定义CSS
        self.apply_custom_css()

        # ---------------------- 调用侧边栏顶部切换功能（关键：在所有侧边栏内容之前执行） ----------------------
        self.add_sidebar_top_navigation()

        # 主标题
        st.markdown("""
<div style="text-align: center; margin: 20px 0;">
    <h1 style="
        background: linear-gradient(135deg, #6a11cb, #ff0080);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        padding: 10px 0;
        text-shadow: 0 5px 15px rgba(106, 17, 203, 0.3);
    ">
    🎸 Air Guitar Advanced - 智能空气吉他
    </h1>
    <p style="
        color: #b8b5d0;
        font-size: 1.1rem;
        margin-top: 5px;
        opacity: 0.9;
    ">
        用手势演奏你的空气吉他，享受音乐创作的乐趣！
    </p>
</div>
""", unsafe_allow_html=True)

        # 渲染原有侧边栏内容
        settings = self.render_sidebar()

        # 初始化摄像头
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            st.error("❌ 无法访问摄像头，请检查摄像头连接")
            st.markdown("""
            <div style="background: rgba(255, 0, 128, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ff0080; margin: 15px 0;">
                <h4 style="color: #ff0080 !important; margin-top: 0;">💡 请确保：</h4>
                <ul style="color: #b8b5d0;">
                    <li>摄像头已连接且未被其他程序占用</li>
                    <li>浏览器已获得摄像头权限</li>
                    <li>摄像头驱动程序正常</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
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
            stop_button = st.button("🛑 停止应用", key=self.get_unique_key("stop"),
                                    use_container_width=True, type="primary")
        with control_col2:
            test_all_button = st.button("🎵 测试所有弦", key=self.get_unique_key("test_all"),
                                        use_container_width=True)
        with control_col3:
            if st.button("🔄 重新开始", key=self.get_unique_key("restart"),
                         use_container_width=True):
                st.rerun()

        # 显示使用指南
        st.markdown("""
        <div style="background: rgba(106, 17, 203, 0.1); padding: 20px; border-radius: 12px; border: 1px solid #6a11cb; margin: 20px 0;">
            <h4 style="color: #00d4ff !important; margin-top: 0;">🎸 使用说明</h4>
            <p style="color: #ffffff; margin-bottom: 10px;">
                <strong>基本操作：</strong>
            </p>
            <ul style="color: #b8b5d0; margin-top: 0;">
                <li>使用<strong style="color: #ff0080;">左手</strong>指定弦（拇指=1, 食指=2, 中指=3, 无名指=4, 小指=5, 握拳=6）</li>
                <li>使用<strong style="color: #00d4ff;">右手</strong>指定品位（竖向1-5对应品1-5，横向1-5对应品6-10）</li>
                <li>双手握拳停止播放</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if test_all_button:
            # 测试所有弦的空弦样本（fret 0）
            st.info("🎶 正在播放所有弦（0品）...")
            for s in range(1, 7):
                try:
                    self.audio_system.play_string_fret(s, 0, volume=self.audio_system.get_volume())
                except Exception:
                    pass
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
                detected_hands = [h for h in results.get('hand_data', []) if h.get('detected')]
                # 若当前帧未检测到任何手，立即清除映射与调试信息，避免显示上一次的结果
                if not detected_hands:
                    try:
                        self.current_string = None
                    except Exception:
                        pass
                    try:
                        self.current_fret = None
                    except Exception:
                        pass
                    try:
                        self.prev_hand_data = []
                    except Exception:
                        pass
                    try:
                        self.debug_info = ""
                    except Exception:
                        pass
                    # 不要清空占位符（会导致页面抖动），只重置内部状态
                    # UI 渲染逻辑会在下方稳定显示“未检测到手部”信息
                # 立即响应指定手势：
                # - 右手握拳 -> 开始播放当前弦/品（若可用）
                # - 双手握拳 -> 结束/停止所有
                # - 手缓慢上升/下降调节音量逻辑在 process_frame 中处理
                try:
                    left_hand = None
                    right_hand = None
                    for h in results.get('hand_data', []):
                        t = h.get('hand_type', '')
                        if str(t).lower().startswith('l'):
                            left_hand = h
                        elif str(t).lower().startswith('r'):
                            right_hand = h
                    # 双手握拳 -> 结束
                    if left_hand and right_hand and left_hand.get('hand_gesture') == 'fist' and right_hand.get(
                            'hand_gesture') == 'fist':
                        try:
                            self.audio_system.stop_all()
                        except Exception:
                            pass
                        self.is_playing = False
                        self.recognition_enabled = False
                        self.debug_info = "双手握拳 - 结束"
                    # 右手握拳 -> 开始（若存在映射）
                    elif right_hand and right_hand.get('hand_gesture') == 'fist':
                        self.recognition_enabled = True
                        try:
                            if self.current_string is not None and self.current_fret is not None:
                                self.is_playing = True
                                self.audio_system.play_string_fret(self.current_string, self.current_fret,
                                                                   volume=self.audio_system.get_volume())
                                self.debug_info = f"右手握拳 - 开始播放 string{self.current_string}_fret{self.current_fret}"
                            else:
                                self.debug_info = "右手握拳 - 未检测到弦/品映射"
                        except Exception:
                            pass
                except Exception:
                    pass

                # 更新FPS
                self.update_fps()

                # 更新UI
                with frame_placeholder.container():
                    col_left, col_center, col_right = st.columns([2, 2, 1])
                    with col_left:
                        st.markdown('<h3 style="color: #ff0080 !important;">👋 手部信息</h3>', unsafe_allow_html=True)
                        hands = [h for h in results.get('hand_data', []) if h.get('detected')]
                        if len(hands) >= 2:
                            # 双手并列 — 两只手都显示详细信息（水平并排）
                            cols_h = st.columns(2)
                            for i, hand in enumerate(hands[:2]):
                                with cols_h[i]:
                                    hand_type = hand.get('hand_type', 'unknown')
                                    color = "#ff0080" if str(hand_type).lower().startswith('l') else "#00d4ff"
                                    st.markdown(
                                        f"<p style='color: {color}; font-weight: bold; margin-bottom: 5px;'>手 {i + 1}: {hand_type}</p>",
                                        unsafe_allow_html=True)
                                    s = hand.get('string', None)
                                    f = hand.get('fret', None)
                                    if s is not None or f is not None:
                                        s_disp = s if s is not None else '-'
                                        f_disp = f if f is not None else '-'
                                        st.write(f"**映射**: 弦 {s_disp}  |  品 {f_disp}")
                                    else:
                                        st.write(f"**和弦**: {hand.get('gesture', 'unknown')}")
                                    features = hand.get('hand_features', {})
                                    extended_count = features.get('extended_count', 0)
                                    st.write(f"**伸直手指**: {extended_count}个")
                                    finger_states = features.get('finger_states', {})
                                    if finger_states:
                                        st.markdown("**手指状态**:")
                                        finger_names = {'thumb': '大拇指', 'index': '食指', 'middle': '中指',
                                                        'ring': '无名指', 'pinky': '小指'}
                                        for finger, state in finger_states.items():
                                            status = "🟢 伸直" if state else "🔴 弯曲"
                                            display_name = finger_names.get(finger, finger)
                                            st.write(f"  {display_name}: {status}")
                        else:
                            # 单手或无手时竖向显示（保留原样）
                            if hands:
                                hand = hands[0]
                                hand_type = hand.get('hand_type', 'unknown')
                                color = "#ff0080" if str(hand_type).lower().startswith('l') else "#00d4ff"
                                st.markdown(
                                    f"<p style='color: {color}; font-weight: bold; margin-bottom: 5px;'>手 1: {hand_type}</p>",
                                    unsafe_allow_html=True)
                                s = hand.get('string', None)
                                f = hand.get('fret', None)
                                if s is not None or f is not None:
                                    s_disp = s if s is not None else '-'
                                    f_disp = f if f is not None else '-'
                                    st.write(f"**映射**: 弦 {s_disp}  |  品 {f_disp}")
                                else:
                                    st.write(f"**和弦**: {hand.get('gesture', 'unknown')}")
                                features = hand.get('hand_features', {})
                                extended_count = features.get('extended_count', 0)
                                st.write(f"**伸直手指**: {extended_count}个")
                                finger_states = features.get('finger_states', {})
                                if finger_states:
                                    st.markdown("**手指状态**:")
                                    finger_names = {'thumb': '大拇指', 'index': '食指', 'middle': '中指',
                                                    'ring': '无名指', 'pinky': '小指'}
                                    for finger, state in finger_states.items():
                                        status = "🟢 伸直" if state else "🔴 弯曲"
                                        display_name = finger_names.get(finger, finger)
                                        st.write(f"  {display_name}: {status}")
                            else:
                                st.warning("👋 未检测到手部，请将手放在摄像头前")
                    with col_center:
                        st.markdown('<h3 style="color: #00d4ff !important;">📷 实时视图</h3>', unsafe_allow_html=True)
                        if results['processed_frame'] is not None:
                            try:
                                st.image(results['processed_frame'], channels="BGR", width=760)
                            except Exception:
                                st.image(results['processed_frame'], channels="BGR", width=760)
                    with col_right:
                        st.markdown('<h3 style="color: #9ad3ff !important;">✨ 特效背景</h3>', unsafe_allow_html=True)
                        try:
                            etype = settings.get('effect_type', 'particles')
                            try:
                                vol = float(self.audio_system.get_volume())
                            except Exception:
                                vol = float(self.config['audio'].get('volume', 0.7))
                            # 为所有特效统一获取渐变色（避免 snow/balloons 使用未定义变量引发异常）
                            c1, c2 = self.get_effect_colors()
                            if etype == 'snow':
                                html = """
                                <canvas id="ag-snow" style="width:100%;height:520px;border-radius:12px;display:block;"></canvas>
                                <script>
                                (function(){
                                    const canvas = document.getElementById('ag-snow');
                                    const ctx = canvas.getContext('2d');
                                    function resize(){ const d=window.devicePixelRatio||1; const r=canvas.getBoundingClientRect(); canvas.width=r.width*d; canvas.height=r.height*d; }
                                    resize(); window.addEventListener('resize', resize);
                                    const gradA = '__GRAD_A__';
                                    const gradB = '__GRAD_B__';
                                    const volume = __VOL__;
                                    function rand(min,max){return Math.random()*(max-min)+min;}
                                    class Snow{constructor(){this.reset();} reset(){this.x=rand(0,canvas.width);this.y=rand(-canvas.height,0);this.r=rand(1,4)*(0.8+volume);this.vy=rand(0.3,1.2);this.alpha=rand(0.4,0.95);} update(){this.y+=this.vy; if(this.y>canvas.height) this.reset();} draw(){ const g = ctx.createLinearGradient(this.x-6,this.y-6,this.x+6,this.y+6); g.addColorStop(0, gradA); g.addColorStop(1, gradB); ctx.fillStyle = g; ctx.globalAlpha = this.alpha; ctx.beginPath(); ctx.arc(this.x,this.y,this.r,0,Math.PI*2); ctx.fill(); ctx.globalAlpha = 1;} }
                                    const flakes=[]; const count=Math.min(200, Math.round(80 + volume*120));
                                    for(let i=0;i<count;i++) flakes.push(new Snow());
                                    function loop(){ ctx.clearRect(0,0,canvas.width,canvas.height); for(const f of flakes){f.update();f.draw();} requestAnimationFrame(loop); }
                                    loop();
                                })();
                                </script>
                                """
                                html = html.replace("__VOL__", f"{vol:.2f}").replace("__GRAD_A__", c1).replace(
                                    "__GRAD_B__", c2)
                            elif etype == 'balloons':
                                html = """
                                <canvas id="ag-balloons" style="width:100%;height:520px;border-radius:12px;display:block;"></canvas>
                                <script>
                                (function(){
                                    const canvas = document.getElementById('ag-balloons');
                                    const ctx = canvas.getContext('2d');
                                    function resize(){ const d=window.devicePixelRatio||1; const r=canvas.getBoundingClientRect(); canvas.width=r.width*d; canvas.height=r.height*d; }
                                    resize(); window.addEventListener('resize', resize);
                                    const gradA = '__GRAD_A__';
                                    const gradB = '__GRAD_B__';
                                    const volume = __VOL__;
                                    function rand(min,max){return Math.random()*(max-min)+min;}
                                    class Balloon{constructor(){this.reset();} reset(){this.x=rand(20,canvas.width-20);this.y=canvas.height+rand(20,400);
                                        // 将气球上升速度调整为与粒子特效相近的量级（较小的垂直位移，加上声音影响）
                                        this.vy = rand(0.2,0.8) * (0.6 + volume);
                                        this.size=rand(12,36);this.h=rand(0,360);} update(){this.y-=this.vy; if(this.y<-120) this.reset();} draw(){ const g=ctx.createRadialGradient(this.x,this.y-this.size/3,1,this.x,this.y,this.size*1.5); g.addColorStop(0, gradA); g.addColorStop(1, gradB); ctx.fillStyle=g; ctx.beginPath(); ctx.ellipse(this.x,this.y,this.size*0.8,this.size,0,0,Math.PI*2); ctx.fill(); ctx.strokeStyle='rgba(0,0,0,0.08)'; ctx.beginPath(); ctx.moveTo(this.x,this.y+this.size); ctx.lineTo(this.x,this.y+this.size+12); ctx.stroke(); } }
                                    const balloons=[]; const count=Math.min(40, Math.round(8 + volume*32));
                                    for(let i=0;i<count;i++) balloons.push(new Balloon());
                                    function loop(){ ctx.clearRect(0,0,canvas.width,canvas.height); for(const b of balloons){b.update(); b.draw();} requestAnimationFrame(loop); }
                                    loop();
                                })();
                                </script>
                                """
                                html = html.replace("__VOL__", f"{vol:.2f}").replace("__GRAD_A__", c1).replace(
                                    "__GRAD_B__", c2)
                            elif etype == 'none':
                                html = "<div style='height:520px;display:flex;align-items:center;justify-content:center;color:#b8b5d0;'>已关闭特效</div>"
                            else:
                                # default particles
                                c1, c2 = self.get_effect_colors()
                                html = """
                                <canvas id="ag-particles" style="width:100%;height:520px;border-radius:12px;display:block;"></canvas>
                                <script>
                                (function(){
                                    const canvas = document.getElementById('ag-particles');
                                    const ctx = canvas.getContext('2d');
                                    function resize(){ const d=window.devicePixelRatio||1; const r=canvas.getBoundingClientRect(); canvas.width=r.width*d; canvas.height=r.height*d; }
                                    resize(); window.addEventListener('resize', resize);
                                    const gradA = '__GRAD_A__';
                                    const gradB = '__GRAD_B__';
                                    const volume = __VOL__;
                                    function rand(min,max){return Math.random()*(max-min)+min;}
                                    class Particle{constructor(){ this.reset(); } reset(){ this.x = rand(0,canvas.width); this.y = rand(canvas.height*0.2, canvas.height); this.vx = rand(-0.4,0.4); this.vy = rand(-0.7,-0.2); this.size = rand(1,8)*(0.6+volume); this.life = rand(80,260); this.age=0; this.alpha=rand(0.4,0.9); } update(){ this.x += this.vx; this.y += this.vy - 0.15*volume; this.age++; if(this.age>this.life || this.y < -50 || this.x < -50 || this.x>canvas.width+50) this.reset(); } draw(){ const g = ctx.createLinearGradient(this.x,this.y,this.x+40,this.y+80); g.addColorStop(0, gradA); g.addColorStop(1, gradB); ctx.fillStyle = g; ctx.globalAlpha = this.alpha * (1 - this.age/this.life); ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI*2); ctx.fill(); ctx.globalAlpha = 1; } }
                                    const particles = []; const count = Math.min(160, Math.round(80 + volume*120));
                                    for(let i=0;i<count;i++) particles.push(new Particle());
                                    function loop(){ ctx.clearRect(0,0,canvas.width,canvas.height); const bg = ctx.createLinearGradient(0,0,canvas.width,canvas.height); bg.addColorStop(0,'rgba(10,10,20,0.35)'); bg.addColorStop(1,'rgba(5,5,15,0.6)'); ctx.fillStyle = bg; ctx.fillRect(0,0,canvas.width,canvas.height); for(const p of particles){ p.update(); p.draw(); } requestAnimationFrame(loop); }
                                    loop();
                                })();
                                </script>
                                """
                                html = html.replace("__VOL__", f"{vol:.2f}").replace("__GRAD_A__", c1).replace(
                                    "__GRAD_B__", c2)
                            import streamlit.components.v1 as components
                            # 将 components 区域高度与 canvas 高度保持一致以拉长显示区域
                            components.html(html, height=560, scrolling=False)
                        except Exception:
                            st.write("✨ 特效加载失败")

                # 更新状态信息（简洁：仅保留指标）
                with status_placeholder.container():
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 FPS", f"{self.fps:.1f}")
                    with col2:
                        st.metric("👋 检测手部", len(results['hand_data']))
                    with col3:
                        try:
                            if getattr(self, 'current_string', None) is not None or getattr(self, 'current_fret',
                                                                                            None) is not None:
                                s_disp = self.current_string if self.current_string is not None else '-'
                                f_disp = self.current_fret if self.current_fret is not None else '-'
                                st.metric("🎯 当前映射", f"弦 {s_disp} | 品 {f_disp}")
                            else:
                                st.metric("🎯 当前映射", "等待中")
                        except Exception:
                            st.metric("🎯 当前映射", "等待中")
                    with col4:
                        try:
                            vol_display = self.audio_system.get_volume()
                        except Exception:
                            vol_display = self.config['audio'].get('volume', 0.7)
                        st.metric("🔊 音量", f"{vol_display:.2f}")

                # 更新和弦显示
                with chord_placeholder.container():
                    self.render_chord_display(results['current_chord'])

                # 更新调试信息
                with debug_placeholder.container():
                    hands = [h for h in results.get('hand_data', []) if h.get('detected')]
                    # 使用统一的 detected_hands；当检测到两只或更多手时，清空调试区（避免重复）
                    if len(detected_hands) >= 2:
                        debug_placeholder.empty()
                    else:
                        # 单手或无手时显示调试信息
                        if self.debug_info:
                            st.info(f"**识别信息**: {self.debug_info}")
                        elif not detected_hands:
                            st.info("**检测状态**: 等待手部检测...")
                        else:  # len(detected_hands) == 1
                            hand = detected_hands[0]
                            features = hand.get('hand_features', {})
                            extended_count = features.get('extended_count', 0)
                            st.info(f"**检测状态**: 检测到手部，伸直{extended_count}个手指")
                # 若有两个或更多手，则此处不再重复显示手部详情（左侧面板已有显示）
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

    def get_effect_colors(self):
        """根据 current_string/current_fret 返回两色渐变 hex"""
        try:
            s = int(self.current_string) if self.current_string else 0
        except Exception:
            s = 0
        try:
            f = int(self.current_fret) if self.current_fret is not None else 0
        except Exception:
            f = 0
        # 弦 -> 基础色相 1..6 映射到不同 hue
        hues = [320, 280, 220, 160, 40, 10]  # 可调整色相分布
        base_h = hues[(s - 1) % len(hues)] if s and 1 <= s <= 6 else 200
        # 品 -> 影响亮度
        light = 40 + min(max(f, 0), 10) * 5  # 40..90
        light2 = max(30, light - 10)
        c1 = f"hsl({base_h} 80% {light}%)"
        c2 = f"hsl({(base_h + 40) % 360} 75% {light2}%)"
        return c1, c2

    def _normalize_hand_type(self, hand: dict) -> str:
        """从 hand（来自 HandTracker）中提取并规范化手型字符串为 'left' 或 'right' 或 ''"""
        keys = ['hand_type', 'handness', 'type', 'label']
        val = ''
        for k in keys:
            v = hand.get(k)
            if isinstance(v, str) and v.strip():
                val = v.strip().lower()
                break
        if 'left' in val or val.startswith('l'):
            return 'left'
        if 'right' in val or val.startswith('r'):
            return 'right'
        return ''

    def _smooth_finger_states(self, hand_type: str, raw_states: dict) -> dict:
        """
        基于最近几帧做多数投票平滑，返回标准顺序的 finger_states 字典。
        raw_states 期望像 {'thumb': True, 'index': False, ...} 这样的映射（键大小写不敏感）。
        """
        if hand_type not in ('left', 'right'):
            # 无法归类则直接返回原始（但确保键名规范化）
            normalized = {k.lower(): bool(v) for k, v in (raw_states or {}).items()}
            # 保持完整键集合
            for k in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                normalized.setdefault(k, False)
            return normalized

        # 规范化 raw_states 键名并补全
        normalized = {k.lower(): bool(v) for k, v in (raw_states or {}).items()}
        for k in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            normalized.setdefault(k, False)

        # push 到历史缓冲并计算多数投票
        hist = self._finger_history.get(hand_type)
        if hist is None:
            hist = deque(maxlen=5)
            self._finger_history[hand_type] = hist
        hist.append(normalized.copy())

        # 如果历史为空（首次），直接返回 normalized
        if not hist:
            return normalized

        # 多数票（True 出现次数 > len(hist)/2）
        counts = {k: 0 for k in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        for frame_states in hist:
            for k, v in frame_states.items():
                if v:
                    counts[k] += 1
        majority = {}
        half = len(hist) / 2.0
        for k in counts:
            majority[k] = counts[k] > half

        # 额外容错：如果所有手指都被判为 False（完全丢失），退回到最近一帧的 normalized（避免全部抹掉）
        if not any(majority.values()):
            majority = normalized

        return majority


def main():
    """主函数"""
    try:
        app = AirGuitarApp()
        app.run()
    except Exception as e:
        st.error(f"❌ 发生错误: {str(e)}")
        st.info("请检查控制台获取详细错误信息")