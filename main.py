import streamlit as st

# Unified single-process app that routes between the three pages
# It imports the three page modules and calls their `main()` functions.

def main():
    st.set_page_config(page_title="Air Guitar - 统一入口", page_icon="🎸", layout="wide")
    
    # 注入自定义CSS样式
    inject_custom_css()
    
    st.sidebar.title("🎸 Air Guitar Pro")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📱 页面切换")
    choice = st.sidebar.radio(
        "选择页面", 
        ["主页 (Home)", "专业版 (Pro)", "新手版 (Novice)"], 
        index=0,
        label_visibility="collapsed"
    )
    
    # 添加一些说明
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ 使用提示", expanded=False):
        st.markdown("""
        **主页**：介绍和版本选择  
        **专业版**：完整功能，适合进阶用户  
        **小白版**：简化功能，适合初学者
        
        ---
        确保：
        - 摄像头正常工作
        - 光线充足
        - 背景简洁
        """)
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Version 2.0 | © 2025 Air Guitar Pro")
    
    if choice == "主页 (Home)":
        # import and run home page
        from home_page import main as home_main
        home_main()
    elif choice == "专业版 (Pro)":
        from main_app import main as pro_main
        pro_main()
    else:
        from main_app1 import main as novice_main
        novice_main()

def inject_custom_css():
    st.markdown("""
    <style>
        /* 主应用背景 */
        .stApp {
            background: linear-gradient(135deg, #0f0c1d 0%, #1a1730 50%, #0f0c1d 100%);
            color: #ffffff;
        }
        
        /* 侧边栏样式 */
        section[data-testid="stSidebar"] {
            background: linear-gradient(135deg, #1a1730, #151225) !important;
            border-right: 1px solid rgba(106, 17, 203, 0.3) !important;
        }

        .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6 {
            color: #ffffff !important;
        }

        .stSidebar p, .stSidebar label, .stSidebar span {
            color: #b8b5d0 !important;
        }
        
        /* 侧边栏单选按钮样式 */
        .stSidebar .stRadio > div {
            background: rgba(26, 23, 48, 0.8);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(106, 17, 203, 0.2);
        }
        
        .stSidebar .stRadio > div > label {
            color: #ffffff !important;
            font-weight: 500;
            padding: 8px 0;
            transition: all 0.3s ease;
        }
        
        .stSidebar .stRadio > div > label:hover {
            color: #00d4ff !important;
            transform: translateX(5px);
        }
        
        .stSidebar .stRadio > div > label[data-baseweb="radio"] > div:first-child {
            border-color: #6a11cb !important;
        }
        
        .stSidebar .stRadio > div > label[data-baseweb="radio"][aria-checked="true"] {
            color: #00d4ff !important;
            font-weight: bold;
        }
        
        .stSidebar .stRadio > div > label[data-baseweb="radio"][aria-checked="true"] > div:first-child {
            background-color: #00d4ff !important;
            border-color: #00d4ff !important;
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
        
        .stSelectbox > div > div > div:hover {
            border-color: #00d4ff !important;
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
        
        /* 侧边栏展开/收起按钮 */
        .stSidebar button[kind="header"] {
            background: #6a11cb !important;
            color: white !important;
        }
        
        .stSidebar button[kind="header"]:hover {
            background: #7a1bdb !important;
        }
        
        /* 可展开区域样式 */
        .streamlit-expanderHeader {
            background: rgba(106, 17, 203, 0.1) !important;
            border: 1px solid rgba(106, 17, 203, 0.3) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: rgba(106, 17, 203, 0.2) !important;
            border-color: #00d4ff !important;
        }
        
        /* 侧边栏分隔线样式 */
        hr {
            border-color: rgba(106, 17, 203, 0.3) !important;
            margin: 20px 0 !important;
        }
        
        /* 响应式调整 */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                width: 250px !important;
            }
        }
        
        /* 滚动条样式 */
        .stSidebar ::-webkit-scrollbar {
            width: 6px;
        }
        
        .stSidebar ::-webkit-scrollbar-track {
            background: rgba(26, 23, 48, 0.5);
        }
        
        .stSidebar ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #6a11cb, #00d4ff);
            border-radius: 3px;
        }
        
        .stSidebar ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #7a1bdb, #10e4ff);
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()