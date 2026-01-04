import streamlit as st
import cv2
import numpy as np
from typing import Dict, Any
import utils

class StreamlitUI:
    """Streamlit用户界面"""
    
    def __init__(self):
        self.setup_page()
        self.button_counter = 0
    
    def setup_page(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="Air Guitar Advanced",
            page_icon="🎸",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 自定义CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #ff6b6b;
            text-align: center;
            margin-bottom: 2rem;
        }
        .guitar-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .status-indicator {
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            text-align: center;
            font-weight: bold;
        }
        .active {
            background-color: #4CAF50;
            color: white;
        }
        .inactive {
            background-color: #f44336;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def get_unique_key(self, base_name: str) -> str:
        """生成唯一的元素key"""
        self.button_counter += 1
        return f"{base_name}_{self.button_counter}"
    
    def render_header(self):
        """渲染页面头部"""
        st.markdown('<h1 class="main-header">🎸 Air Guitar Advanced</h1>', unsafe_allow_html=True)
        st.markdown("### 用空气弹奏真实的吉他！")
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("设置")
            
            # 音频设置
            st.subheader("音频设置")
            volume = st.slider("音量", 0.0, 1.0, 0.7, key=self.get_unique_key("volume"))
            audio_latency = st.slider("音频延迟", 0, 200, 50, 10, key=self.get_unique_key("latency"))
            
            # 视觉设置
            st.subheader("视觉设置")
            show_landmarks = st.checkbox("显示手部关键点", value=True, key=self.get_unique_key("landmarks"))
            show_3d_view = st.checkbox("显示3D视图", value=True, key=self.get_unique_key("3dview"))
            particle_effects = st.checkbox("粒子效果", value=True, key=self.get_unique_key("particles"))
            
            # 吉他设置
            st.subheader("吉他设置")
            guitar_tuning = st.selectbox("调弦", ["标准调弦", "降D调弦", "开放G调弦"], key=self.get_unique_key("tuning"))
            string_sensitivity = st.slider("弦灵敏度", 1, 10, 5, key=self.get_unique_key("sensitivity"))
            
            return {
                'volume': volume,
                'audio_latency': audio_latency,
                'show_landmarks': show_landmarks,
                'show_3d_view': show_3d_view,
                'particle_effects': particle_effects,
                'guitar_tuning': guitar_tuning,
                'string_sensitivity': string_sensitivity
            }
    
    def render_camera_view(self, frame, hand_data):
        """渲染相机视图"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("实时相机视图")
            if frame is not None:
                # 调整图像大小以适应显示
                frame_resized = cv2.resize(frame, (640, 480))
                st.image(frame_resized, channels="BGR", width='stretch')
        
        with col2:
            st.subheader("手部信息")
            if hand_data:
                for i, hand in enumerate(hand_data):
                    with st.container():
                        st.write(f"手 {i+1}: {hand.get('type', 'unknown')}")
                        st.write(f"手势: {hand.get('gesture', 'unknown')}")
                        
                        # 显示手指位置
                        finger_tips = hand.get('finger_tips', {})
                        for finger, pos in finger_tips.items():
                            st.write(f"{finger}: ({pos[0]:.2f}, {pos[1]:.2f})")
            else:
                st.warning("未检测到手部")
    
    def render_3d_view(self):
        """渲染3D视图占位符"""
        st.subheader("3D吉他视图")
        st.info("3D视图将在主应用中显示")
    
    def render_audio_controls(self, audio_system):
        """渲染音频控制"""
        st.subheader("音频控制")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("测试音频", key=self.get_unique_key("test_audio"), width='stretch'):
                if audio_system:
                    audio_system.play_note("A", 0.5)
        
        with col2:
            if st.button("停止所有音频", key=self.get_unique_key("stop_audio"), width='stretch'):
                if audio_system:
                    audio_system.stop_all()
        
        with col3:
            if audio_system:
                current_volume = audio_system.get_volume()
                st.write(f"当前音量: {current_volume:.1f}")
            else:
                st.write("音频系统未就绪")
    
    def render_status_indicator(self, is_tracking: bool, fps: float):
        """渲染状态指示器"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_class = "active" if is_tracking else "inactive"
            status_text = "运行中" if is_tracking else "未运行"
            st.markdown(f'<div class="status-indicator {status_class}">手部追踪: {status_text}</div>', 
                       unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="status-indicator active">FPS: {fps:.1f}</div>', 
                       unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="status-indicator active">音频: 就绪</div>', 
                       unsafe_allow_html=True)
    
    def render_chord_display(self, current_chord: str):
        """渲染当前和弦显示"""
        if current_chord and current_chord != "none" and current_chord != "unknown":
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #ff6b6b, #ee5a24); 
                        border-radius: 10px; margin: 10px 0;">
                <h2 style="color: white; margin: 0;">当前和弦: {current_chord}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    def render_main_interface(self, frame, hand_data, audio_system, current_chord: str, 
                            is_tracking: bool, fps: float):
        """渲染主界面"""
        self.render_header()
        
        # 获取设置
        settings = self.render_sidebar()
        
        # 状态指示器
        self.render_status_indicator(is_tracking, fps)
        
        # 和弦显示
        self.render_chord_display(current_chord)
        
        # 主内容区
        self.render_camera_view(frame, hand_data)
        self.render_audio_controls(audio_system)
        
        if settings['show_3d_view']:
            self.render_3d_view()
        
        return settings
