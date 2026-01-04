# config.py - 应用配置
import os

class Config:
    """应用配置类"""
    
    # 应用设置
    APP_TITLE = "Air Guitar 3D - 虚拟吉他"
    APP_ICON = "🎸"
    
    # 摄像头设置
    CAMERA_ID = 0
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    # 手部检测设置
    HAND_DETECTION_CONFIDENCE = 0.7
    HAND_TRACKING_CONFIDENCE = 0.5
    MAX_HANDS = 2
    
    # 手势识别设置
    GESTURE_SMOOTHING = 5
    MIN_GESTURE_CONFIDENCE = 0.6
    
    # 界面设置
    THEME = "dark"
    SIDEBAR_STATE = "expanded"
    
    @classmethod
    def get_camera_settings(cls):
        """获取摄像头设置"""
        return {
            'camera_id': cls.CAMERA_ID,
            'width': cls.FRAME_WIDTH,
            'height': cls.FRAME_HEIGHT
        }
