import numpy as np
from typing import List, Dict, Tuple, Any
import utils

class GestureAnalyzer:
    """手势分析与和弦识别"""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = utils.load_config()
            
        self.guitar_config = config['guitar']
        self.chords_config = config['chords']
        
    def analyze_hand_position(self, hand_data: Dict, image_shape: Tuple[int, int]) -> Dict[str, Any]:
        """分析手部位置并映射到吉他指板"""
        if not hand_data:
            return {'detected': False}
        
        landmarks = hand_data['landmarks']
        # 优先使用 hand_data 中预计算的 finger_states（由 HandTracker.detect_fingers_extended 提供）
        precomputed_states = hand_data.get('finger_states')
        finger_tips = self.get_finger_tips(landmarks)
        
        # 计算手部边界框
        x_coords = [lm[0] for lm in landmarks]
        y_coords = [lm[1] for lm in landmarks]
        
        hand_bbox = {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
        
        # 计算手部特征；若已有预计算的 finger_states 则优先使用
        hand_features = self.calculate_hand_features(finger_tips, landmarks, precomputed_states)
        
        # 识别和弦
        chord = self.recognize_chord_by_count_and_position(hand_features, hand_bbox)
        
        return {
            'detected': True,
            'hand_type': hand_data['type'],
            'finger_tips': finger_tips,
            'bounding_box': hand_bbox,
            'hand_features': hand_features,
            'gesture': chord
        }
    
    def get_finger_tips(self, landmarks: List[Tuple[float, float, float]]) -> Dict[str, Tuple[float, float]]:
        """获取手指尖端坐标"""
        return {
            'thumb': (landmarks[4][0], landmarks[4][1]),
            'index': (landmarks[8][0], landmarks[8][1]),
            'middle': (landmarks[12][0], landmarks[12][1]),
            'ring': (landmarks[16][0], landmarks[16][1]),
            'pinky': (landmarks[20][0], landmarks[20][1])
        }
    
    def calculate_hand_features(self, finger_tips: Dict, landmarks: List, precomputed_states: Dict = None) -> Dict[str, Any]:
        """计算手部特征"""
        features = {}
        
        # 计算每个手指的伸直状态（包含拇指）
        if precomputed_states and isinstance(precomputed_states, dict):
            finger_states = precomputed_states
        else:
            finger_states = {}
            for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                if finger == 'thumb':
                    finger_states['thumb'] = self.is_thumb_extended(landmarks)
                else:
                    finger_states[finger] = self.is_finger_extended_simple(finger, landmarks)
        
        features['finger_states'] = finger_states
        
        # 计算伸直手指数量（包含拇指）
        extended_count = sum(1 for state in finger_states.values() if state)
        # 不包含拇指的伸直手指计数（用于右手品位映射，按用户要求1-5对应品位）
        extended_count_no_thumb = sum(1 for k, state in finger_states.items() if k != 'thumb' and state)
        features['extended_count'] = extended_count
        features['extended_count_no_thumb'] = extended_count_no_thumb
        
        # 计算伸直手指的组合
        extended_fingers = [finger for finger, state in finger_states.items() if state]
        features['extended_fingers'] = extended_fingers
        
        # 调试信息
        print(f"手指状态: {finger_states}")
        print(f"伸直手指: {extended_fingers} (共{extended_count}个)")
        
        return features

    def is_thumb_extended(self, landmarks: List) -> bool:
        """基于拇指关键点位置的简化伸直判断"""
        # 使用归一化手部跨度判断拇指是否伸直，避免固定阈值在不同距离下失效
        try:
            tip = landmarks[4]
            base = landmarks[2]
            xs = [lm[0] for lm in landmarks]
            ys = [lm[1] for lm in landmarks]
            hand_span = max(max(xs) - min(xs), max(ys) - min(ys))
            if hand_span <= 0:
                return False
            distance = ((tip[0] - base[0])**2 + (tip[1] - base[1])**2) ** 0.5
            # 归一化距离比率，经验阈值 0.25
            return (distance / hand_span) > 0.25
        except Exception:
            return False

    def map_left_hand_to_string(self, features: Dict) -> int:
        """将左手手型映射为弦序号（1-6）。
        规则：拇指->1，食指->2，中指->3，无名指->4，小指->5；若检测到握拳或无伸直手指，则视为第6弦。"""
        fs = features.get('finger_states', {})
        if not fs:
            return 6

        mapping = {
            'thumb': 1,
            'index': 2,
            'middle': 3,
            'ring': 4,
            'pinky': 5
        }

        # 若多个手指伸直，优先选择伸直的最靠近手掌外侧的手指（按顺序thumb->index->middle->ring->pinky）
        for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            if fs.get(finger, False):
                return mapping[finger]

        # 若无伸直手指，视为握拳 -> 第6弦
        return 6

    def determine_fret_from_right_hand(self, features: Dict, landmarks: List) -> int:
        """根据右手伸指数和手的朝向计算品位（0-10）。
        规则：竖向 -> 1-5指对应品1-5；横向 -> 1-5指对应品6-10；若无伸指 -> 0品（空弦）。"""
        # 使用手的垂直位置（画面上下半区）来决定映射规则（用户要求）:
        # - 下半区（手部垂直中心 >= 0.5）: 伸出手指数 1-5 -> 品 1-5
        # - 上半区（手部垂直中心 < 0.5）: 伸出手指数 1-5 -> 品 6-10
        # 优先使用包含拇指的计数，使拇指也能影响品位；若为0再回退到不含拇指的计数。
        extended_no_thumb = features.get('extended_count_no_thumb', 0)
        extended_with_thumb = features.get('extended_count', extended_no_thumb)

        # 计算手部垂直中心（使用 landmarks 的平均 y，坐标为归一化 [0,1]）
        try:
            ys = [lm[1] for lm in landmarks]
            vert_center = sum(ys) / len(ys) if ys else 0.5
        except Exception:
            vert_center = 0.5

        # 选择计数：优先不含拇指
        # 选择计数：优先包含拇指
        if extended_with_thumb and extended_with_thumb > 0:
            extended = int(extended_with_thumb)
        elif extended_no_thumb and extended_no_thumb > 0:
            extended = int(extended_no_thumb)
        else:
            return 0

        # 限制到 1-5 的有效范围
        extended = max(1, min(5, extended))

        # 根据用户要求：下半区 -> 品1-5；上半区 -> 品6-10
        if vert_center >= 0.5:
            # 下半区 -> 品 1-5
            fret = min(5, extended)
            print(f"DEBUG_FRET_MAP: vert_center={vert_center:.3f} -> LOWER half -> extended={extended} -> fret={fret}")
            return fret
        else:
            # 上半区 -> 品 6-10
            fret = min(10, 5 + extended)
            print(f"DEBUG_FRET_MAP: vert_center={vert_center:.3f} -> UPPER half -> extended={extended} -> fret={fret}")
            return fret
    
    def is_finger_extended_simple(self, finger: str, landmarks: List) -> bool:
        """简化的手指伸直检测"""
        # 手指关键点索引
        finger_indices = {
            'index': [5, 6, 7, 8],
            'middle': [9, 10, 11, 12],
            'ring': [13, 14, 15, 16],
            'pinky': [17, 18, 19, 20]
        }
        
        if finger not in finger_indices:
            return False
        
        indices = finger_indices[finger]
        
        # 使用指节间距比率判断：若指尖相对于近端关节明显伸出则认为伸直
        # indices = [mcp, pip, dip, tip]
        mcp = landmarks[indices[0]]
        pip = landmarks[indices[1]]
        tip = landmarks[indices[3]]

        # 计算 pip-mcp 与 tip-pip 的距离比
        def dist(a, b):
            return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

        pip_mcp = dist(pip, mcp)
        tip_pip = dist(tip, pip)

        if pip_mcp <= 0:
            return False

        ratio = tip_pip / pip_mcp
        # 当 tip_pip 明显大于 pip_mcp 时认为手指伸直；降低误判对抖动敏感的情况
        return ratio > 0.7
    
    def recognize_chord_by_count_and_position(self, features: Dict, bbox: Dict) -> str:
        """基于手指数量和位置识别和弦"""
        extended_count = features['extended_count']
        hand_position = self.get_hand_position(bbox)
        
        print(f"调试信息: 伸直手指数={extended_count}, 位置={hand_position}")
        
        # 基于伸直手指数量和位置的识别
        # C大调：两指伸直，手部在较高位置
        if extended_count == 2 and hand_position == 'high':
            print("✅ 识别为 C大调: 两指伸直 + 手部抬高")
            return 'C_major'
        
        # G大调：两指伸直，手部在较低位置
        elif extended_count == 2 and hand_position == 'low':
            print("✅ 识别为 G大调: 两指伸直 + 手部放低")
            return 'G_major'
        
        # D大调：三指伸直，手部在较高位置
        elif extended_count == 3 and hand_position == 'high':
            print("✅ 识别为 D大调: 三指伸直 + 手部抬高")
            return 'D_major'
        
        # A小调：三指伸直，手部在较低位置
        elif extended_count == 3 and hand_position == 'low':
            print("✅ 识别为 A小调: 三指伸直 + 手部放低")
            return 'A_minor'
        
        # E小调：四指伸直，手部在较高位置
        elif extended_count == 4 and hand_position == 'high':
            print("✅ 识别为 E小调: 四指伸直 + 手部抬高")
            return 'E_minor'
        
        # F大调：四指伸直，手部在较低位置
        elif extended_count == 4 and hand_position == 'low':
            print("✅ 识别为 F大调: 四指伸直 + 手部放低")
            return 'F_major'
        
        print(f"❌ 未识别: 伸直{extended_count}指, 位置{hand_position}")
        return "unknown"
    
    def get_hand_position(self, bbox: Dict) -> str:
        """获取手部位置（高/中/低）"""
        vertical_center = (bbox['y_min'] + bbox['y_max']) / 2
        
        print(f"手部垂直位置: {vertical_center}")
        
        # 调整位置阈值，让"高"位置更容易识别
        if vertical_center < 0.5:  # 从0.4调整到0.5
            return 'high'
        elif vertical_center < 0.7:
            return 'middle'
        else:
            return 'low'
    
    def calculate_strumming_direction(self, prev_hand_data: Dict, current_hand_data: Dict) -> str:
        """计算扫弦方向"""
        if not prev_hand_data or not current_hand_data:
            return "none"
        
        if not prev_hand_data.get('detected', False) or not current_hand_data.get('detected', False):
            return "none"
            
        prev_y = prev_hand_data['bounding_box']['y_min']
        current_y = current_hand_data['bounding_box']['y_min']
        
        movement = current_y - prev_y
        
        if movement > 0.05:
            return "downstroke"
        elif movement < -0.05:
            return "upstroke"
        else:
            return "none"
