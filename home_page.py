import streamlit as st
import os
import sys

# 页面配置将由 main() 在运行时设置，以便在统一应用中复用


# ---------------------- 修改：侧边栏操作指南功能 ----------------------
def add_sidebar_navigation():
    st.sidebar.markdown("### 📚 操作指南")
    st.sidebar.markdown("---")       
    
    # 小白版和弦指南
    with st.sidebar.expander("🎯新手版和弦指南", expanded=False):
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
        
        for chord_name, chord_info in chords_guide.items():
            with st.container():
                col_icon, col_text = st.columns([1, 4])
                with col_icon:
                    st.markdown(f"<div style='font-size: 1.5rem;'>{chord_info['icon']}</div>", unsafe_allow_html=True)
                with col_text:
                    st.markdown(f"**{chord_name.replace('_', ' ').title()}**")
                    st.caption(chord_info['instruction'])
                st.divider()
    
    # 专业版映射表
    with st.sidebar.expander("🎸 专业版映射表", expanded=False):
        tab1, tab2, tab3 = st.tabs(["0品", "1-5品", "6-10品"])
        
        with tab1:
            st.markdown("**0品：无右手显示**")
            st.markdown("""
            | 左手手势 | 弦序号 | 音名 | 频率(Hz) |
            |----------|--------|------|----------|
            | 拇指 | 1 | e¹ | 329.63 |
            | 食指 | 2 | B | 246.94 |
            | 中指 | 3 | G | 196.00 |
            | 无名指 | 4 | D | 146.83 |
            | 小指 | 5 | A | 110.00 |
            | 握拳 | 6 | E | 82.41 |
            """)
        
        with tab2:
            st.markdown("**1-5品：右手竖向手指数**")
            st.markdown("""
            | 左手手势 | 弦 | 右手手势 | 品 | 音名 |
            |----------|-----|----------|-----|------|
            | 拇指 | 1 | 竖向1指 | 1 | #e¹ |
            | 拇指 | 1 | 竖向2指 | 2 | f¹ |
            | 拇指 | 1 | 竖向3指 | 3 | g¹ |
            | 拇指 | 1 | 竖向4指 | 4 | #g¹ |
            | 拇指 | 1 | 竖向5指 | 5 | a¹ |
            | ... | ... | ... | ... | ... |
            """)
            st.caption("详细表格见应用内说明")
        
        with tab3:
            st.markdown("**6-10品：右手横向手指数**")
            st.markdown("""
            | 左手手势 | 弦 | 右手手势 | 品 | 音名 |
            |----------|-----|----------|-----|------|
            | 拇指 | 1 | 横向1指 | 6 | #a¹ |
            | 拇指 | 1 | 横向2指 | 7 | b¹ |
            | 拇指 | 1 | 横向3指 | 8 | c² |
            | 拇指 | 1 | 横向4指 | 9 | #c² |
            | 拇指 | 1 | 横向5指 | 10 | d² |
            | ... | ... | ... | ... | ... |
            """)
            st.caption("详细表格见应用内说明")
    
    st.sidebar.markdown("---")

# `add_sidebar_navigation()` 不在模块导入时自动运行，改由 `main()` 在渲染时调用。


# ---------------------- 修改CSS样式，将侧边栏字体颜色改为粉色 ----------------------
def inject_custom_css():
    st.markdown("""
    <style>
        /* 主背景和文本颜色 */
        .stApp {
            background: linear-gradient(135deg, #0f0c1d 0%, #1a1730 50%, #0f0c1d 100%);
            color: #ffffff;
        }

        /* 侧边栏文本颜色 - 改为粉色主题 */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown div,
        section[data-testid="stSidebar"] .st-expander,
        section[data-testid="stSidebar"] .st-expander label,
        section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"],
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] .st-emotion-cache-16txtl3,
        section[data-testid="stSidebar"] .st-emotion-cache-10trblm {
            color: #ff6b9d !important;  /* 粉色文字 */
        }
        
        /* 侧边栏标题和特殊强调 */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #ff0080 !important;  /* 更深的粉色 */
            text-shadow: 0 2px 5px rgba(255, 0, 128, 0.3);
        }
        
        /* 侧边栏加粗文本 */
        section[data-testid="stSidebar"] strong,
        section[data-testid="stSidebar"] b {
            color: #ff3399 !important;
        }
        
        /* 侧边栏表格颜色 */
        section[data-testid="stSidebar"] table,
        section[data-testid="stSidebar"] th,
        section[data-testid="stSidebar"] td {
            color: #ffb6d9 !important;  /* 浅粉色 */
            border-color: rgba(255, 107, 157, 0.5) !important;
        }
        
        /* 侧边栏链接和特殊文本 */
        section[data-testid="stSidebar"] a,
        section[data-testid="stSidebar"] .st-emotion-cache-1c7y2kd {
            color: #ff3399 !important;
        }
        
        /* 侧边栏分隔线和边框 */
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255, 107, 157, 0.3) !important;
        }
        
        /* 侧边栏背景渐变（粉色主题） */
        section[data-testid="stSidebar"] {
            background: linear-gradient(135deg, rgba(26, 23, 48, 0.95) 0%, rgba(255, 0, 128, 0.1) 100%) !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 107, 157, 0.3);
        }
        
        /* 侧边栏可展开区域 */
        section[data-testid="stSidebar"] .st-emotion-cache-1c7y2kd {
            background-color: rgba(255, 107, 157, 0.15) !important;
            border: 1px solid rgba(255, 107, 157, 0.3) !important;
            border-radius: 10px !important;
            margin-bottom: 10px !important;
        }
        
        section[data-testid="stSidebar"] .st-emotion-cache-1c7y2kd:hover {
            background-color: rgba(255, 107, 157, 0.25) !important;
            border-color: #ff0080 !important;
        }
        
        /* 侧边栏标签页样式 */
        section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 107, 157, 0.1) !important;
            border-radius: 8px 8px 0 0 !important;
            margin: 0 2px !important;
            color: #ffb6d9 !important;
        }
        
        section[data-testid="stSidebar"] .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(255, 0, 128, 0.2) !important;
            color: #ff0080 !important;
            font-weight: bold !important;
        }
        
        /* 按钮样式 */
        .stButton > button {
            width: 100%;
            height: 100px;
            font-size: 1.5rem !important;
            font-weight: bold !important;
            border-radius: 15px !important;
            border: 3px solid transparent !important;
            background: linear-gradient(135deg, #6a11cb, #ff0080) !important;
            color: white !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 20px rgba(106, 17, 203, 0.3) !important;
        }

        .stButton > button:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 12px 25px rgba(106, 17, 203, 0.5) !important;
            border-color: #00d4ff !important;
        }

        /* 侧边栏切换按钮样式（单独优化） */
        .stSidebar .stButton > button {
            height: 60px !important;
            font-size: 1.1rem !important;
            margin-bottom: 10px !important;
            background: linear-gradient(135deg, #ff0080, #ff6b9d) !important; /* 粉色渐变 */
        }

        .stSidebar .stButton > button:hover {
            border-color: #ffb6d9 !important;
        }

        /* 卡片样式 */
        .version-card {
            background: rgba(26, 23, 48, 0.8);
            border-radius: 20px;
            padding: 30px;
            border: 2px solid rgba(106, 17, 203, 0.3);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            height: 100%;
        }

        .version-card:hover {
            transform: translateY(-10px);
            border-color: #00d4ff;
            box-shadow: 0 15px 35px rgba(0, 212, 255, 0.2);
        }

        /* 标题样式 */
        .main-title {
            background: linear-gradient(135deg, #6a11cb, #ff0080, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            font-size: 4rem !important;
            font-weight: 800 !important;
            margin-bottom: 10px !important;
            text-shadow: 0 5px 15px rgba(106, 17, 203, 0.3);
        }

        .subtitle {
            color: #b8b5d0;
            text-align: center;
            font-size: 1.3rem;
            margin-bottom: 50px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        /* 特色图标样式 */
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }

        /* 版本标签 */
        .version-tag {
            display: inline-block;
            background: linear-gradient(135deg, #ff0080, #ff6b9d);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 15px;
        }

        /* 响应式调整 */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2.5rem !important;
            }

            .stButton > button {
                height: 80px;
                font-size: 1.2rem !important;
            }

            .stSidebar .stButton > button {
                height: 50px !important;
                font-size: 1rem !important;
            }
            
            /* 移动端侧边栏调整 */
            section[data-testid="stSidebar"] {
                width: 85% !important;
            }
        }

        /* 移除默认的空白 */
        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
        }

        /* 移除原有的侧边栏隐藏样式（关键修改） */
        /* section[data-testid="stSidebar"] {
            display: none;
        } */

        /* 页脚样式 */
        .footer {
            color: #b8b5d0;
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)


def create_feature_grid():
    """创建功能特性网格"""
    features = [
        {
            "icon": "🤖",
            "title": "手势识别",
            "desc": "基于深度学习的手势识别技术，精准识别各类吉他手势"
        },
        {
            "icon": "🎵",
            "title": "真实音效",
            "desc": "高保真吉他音色采样，还原真实演奏体验"
        },
        {
            "icon": "🎮",
            "title": "实时反馈",
            "desc": "即时视觉反馈，让学习过程更有趣"
        },
        {
            "icon": "📊",
            "title": "性能监控",
            "desc": "实时FPS显示和系统状态监控"
        }
    ]

    cols = st.columns(4)
    for idx, feature in enumerate(features):
        with cols[idx]:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: rgba(106, 17, 203, 0.1); 
                        border-radius: 15px; border: 1px solid rgba(106, 17, 203, 0.3);">
                <div class="feature-icon">{feature['icon']}</div>
                <h4 style="color: #ffffff; margin-bottom: 10px;">{feature['title']}</h4>
                <p style="color: #b8b5d0; font-size: 0.9rem;">{feature['desc']}</p>
            </div>
            """, unsafe_allow_html=True)


def create_version_cards():
    """创建版本选择卡片"""
    cols = st.columns(2)

    with cols[0]:
        st.markdown("""
        <div class="version-card">
            <div class="version-tag">专业版</div>
            <h2 style="color: #00d4ff; margin-bottom: 20px;">🎸 PRO 专业版</h2>
            <p style="color: #b8b5d0; margin-bottom: 25px;">
                为专业玩家设计的高级模式，提供完整的弦品映射功能，支持复杂的演奏技巧。
            </p>
            <div style="margin-bottom: 25px;">
                <p style="color: #ffffff; margin-bottom: 10px;"><strong>✨ 特色功能：</strong></p>
                <ul style="color: #b8b5d0; padding-left: 20px;">
                    <li>完整的6弦映射（1-6弦）</li>
                    <li>多品位支持（0-10品）</li>
                    <li>双手独立控制</li>
                    <li>扫弦动作识别</li>
                    <li>音量手势控制</li>
                    <li>实时调试信息</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 专业版按钮
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🚀 启动专业版", key="pro_start", use_container_width=True):
                # 跳转到专业版
                os.system("streamlit run main_app.py")

    with cols[1]:
        st.markdown("""
        <div class="version-card">
            <div class="version-tag" style="background: linear-gradient(135deg, #00d4ff, #6a11cb);">小白版</div>
            <h2 style="color: #ff0080; margin-bottom: 20px;">🎯 NOVICE 新手版</h2>
            <p style="color: #b8b5d0; margin-bottom: 25px;">
                适合初学者的简化模式，只需做出简单手势即可演奏和弦，快速上手体验。
            </p>
            <div style="margin-bottom: 25px;">
                <p style="color: #ffffff; margin-bottom: 10px;"><strong>✨ 特色功能：</strong></p>
                <ul style="color: #b8b5d0; padding-left: 20px;">
                    <li>6种基础和弦识别</li>
                    <li>手势位置检测</li>
                    <li>一键测试功能</li>
                    <li>简化操作界面</li>
                    <li>实时视觉反馈</li>
                    <li>内置学习指南</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 小白版按钮
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn2:
            if st.button("🎈 启动小白版", key="novice_start", use_container_width=True):
                # 跳转到小白版
                os.system("streamlit run main_app1.py")


def main():
    """主函数"""
    st.set_page_config(
        page_title="Air Guitar Pro - 智能空气吉他",
        page_icon="🎸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # 在主函数开始时添加侧边栏导航
    add_sidebar_navigation()
    # 注入CSS样式
    inject_custom_css()

    # 主标题区域
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 class="main-title">🎸 AIR GUITAR PRO</h1>
        <p class="subtitle">
            基于计算机视觉的智能空气吉他演奏系统<br>
            无需实体吉他，通过手势即可演奏美妙音乐
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 功能特性展示
    st.markdown("<br>", unsafe_allow_html=True)
    create_feature_grid()

    # 版本选择区域
    st.markdown("""
    <div style="text-align: center; margin: 60px 0 30px 0;">
        <h2 style="color: #ffffff; font-size: 2.5rem; margin-bottom: 10px;">选择您的版本</h2>
        <p style="color: #b8b5d0; max-width: 600px; margin: 0 auto;">
            根据您的经验水平选择合适的版本开始演奏
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 创建版本卡片
    create_version_cards()

    # 使用说明
    with st.expander("📖 使用说明", expanded=False):
        st.markdown("""
        ### 🎯 快速开始指南

        **硬件要求：**
        - 电脑摄像头（建议720p以上分辨率）
        - 麦克风或音频输出设备
        - 良好的光线环境

        **软件要求：**
        - Python 3.8+
        - 安装所有依赖包：`pip install -r requirements.txt`

        **准备步骤：**
        1. 确保摄像头对准您的手部
        2. 保持适当距离（手臂完全伸展在画面中）
        3. 确保光线充足，手部清晰可见
        4. 根据选择的版本，按照界面提示操作

        **专业版特别说明：**
        - 左手控制弦位（1-6弦）
        - 右手控制品位（0-10品）
        - 握拳手势控制播放/停止
        - 上下移动调节音量
        """)

    # 页脚
    st.markdown("""
    <div class="footer">
        <p>🎵 Air Guitar Pro © 2024 | 基于计算机视觉的智能音乐演奏系统</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">Version 2.0 | 使用Streamlit构建</p>
    </div>
    """, unsafe_allow_html=True)

    # 已移除可能与 Streamlit 渲染冲突的内联脚本（如需交互效果，请使用 components.html 或自定义 Streamlit 组件）
    st.markdown("""
    <!-- Inline scripts removed to avoid Streamlit DOM conflicts.
         If you want similar interactive visuals, wrap them with
         `streamlit.components.v1.html(...)` or implement a proper
         Streamlit component that handles mount/unmount cleanup. -->
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()