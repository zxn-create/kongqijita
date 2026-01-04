# gesture_analyzer.py - 修复版手势分析器
import numpy as np
import logging
from utils import config

logger = logging.getLogger("GestureAnalyzer")

class GestureAnalyzer:
    """手势分析器 - 修复导入问题"""
    
    def __init__(self, smoothness=None):
        self.smoothness = smoothness or config.GESTURE_SMOOTHING
        self.gesture_history = []
        self.current_gesture = "未知"
        
        # 手势定义
        self.GESTURES = {
            'fist': '拳头',
            'open_hand': '张开手', 
            'pointing': '指向',
            'peace': '和平手势',
            'rock': '摇滚手势',
            'thumbs_up': '大拇指',
            'guitar_chord': '吉他和弦'
        }
        
        logger.info("✅ 手势分析器初始化完成")

    def analyze_hand_landmarks(self, hand_info):
        """分析手部关键点识别手势"""
        if hand_info is None:
            return "未检测到手部"
        
        gesture = self._basic_gesture_recognition(hand_info)
        
        # 添加到历史记录
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.smoothness:
            self.gesture_history.pop(0)
        
        # 平滑处理
        self.current_gesture = self._smooth_gesture()
        return self.current_gesture

    def _basic_gesture_recognition(self, hand_info):
        """基础手势识别"""
        if hand_info.get('detection_method') == 'mediapipe':
            return self._analyze_mediapipe_gesture(hand_info)
        else:
            return self._analyze_fallback_gesture(hand_info)

    def _analyze_mediapipe_gesture(self, hand_info):
        """分析MediaPipe手势"""
        keypoints = hand_info.get('keypoints', [])
        if len(keypoints) < 21:
            return "关键点不足"
        
        # 计算手指伸直状态
        extended_fingers = self._count_extended_fingers(keypoints)
        
        # 手势判断
        if extended_fingers == 0:
            return "拳头"
        elif extended_fingers == 5:
            return "张开手"
        elif extended_fingers == 1:
            return "指向"
        elif extended_fingers == 2:
            return "和平手势"
        elif extended_fingers == 3:
            return "三指手势"
        elif extended_fingers == 4:
            return "四指手势"
        else:
            return f"{extended_fingers}指手势"

    def _count_extended_fingers(self, keypoints):
        """计算伸直的手指数量"""
        finger_tips = [8, 12, 16, 20]  # 食、中、无、小指尖
        finger_pips = [6, 10, 14, 18]  # 近端指向关节
        
        extended_count = 0
        for tip_idx, pip_idx in zip(finger_tips, finger_pips):
            if tip_idx < len(keypoints) and pip_idx < len(keypoints):
                tip = keypoints[tip_idx]
                pip = keypoints[pip_idx]
                
                # 计算距离
                tip_to_pip_distance = abs(tip['y'] - pip['y'])
                if tip_to_pip_distance > 20:  # 阈值可调整
                    extended_count += 1
        
        return extended_count

    def _analyze_fallback_gesture(self, hand_info):
        """分析备用检测手势"""
        area = hand_info.get('area', 0)
        compactness = hand_info.get('compactness', 0)
        
        if compactness > 0.7:
            return "拳头"
        elif compactness < 0.3:
            return "张开手"
        elif area < 8000:
            return "小手势"
        else:
            return "大手势"

    def _smooth_gesture(self):
        """手势平滑处理"""
        if not self.gesture_history:
            return "未知"
        
        # 选择出现次数最多的手势
        from collections import Counter
        gesture_counts = Counter(self.gesture_history)
        return gesture_counts.most_common(1)[0][0]

    def get_guitar_chord(self, gesture, hand_position):
        """根据手势获取吉他和弦"""
        chord_mapping = {
            "拳头": "C和弦",
            "张开手": "G和弦", 
            "指向": "Em和弦",
            "和平手势": "Am和弦",
            "大拇指": "D和弦",
            "三指手势": "F和弦",
            "四指手势": "A和弦"
        }
        
        return chord_mapping.get(gesture, "未知和弦")

class GuitarChordDetector:
    """吉他和弦检测器"""
    
    def __init__(self):
        self.chord_history = []
    
    def detect_chord(self, left_hand_gesture, right_hand_gesture):
        """检测和弦基于双手手势"""
        if left_hand_gesture == "未知" or right_hand_gesture == "未知":
            return "等待双手输入"
        
        # 简化的和弦映射
        chord_map = {
            ("拳头", "张开手"): "C大调",
            ("张开手", "拳头"): "G大调", 
            ("指向", "和平手势"): "Em小调",
            ("和平手势", "指向"): "Am小调",
            ("拳头", "拳头"): "强力五和弦",
            ("张开手", "张开手"): "开放和弦"
        }
        
        return chord_map.get((left_hand_gesture, right_hand_gesture), "自定义和弦")
