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
        
        # 计算手部特征
        hand_features = self.calculate_hand_features(finger_tips, landmarks)
        
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
    
    def calculate_hand_features(self, finger_tips: Dict, landmarks: List) -> Dict[str, Any]:
        """计算手部特征"""
        features = {}
        
        # 计算每个手指的伸直状态（包含拇指）
        finger_states = {}
        for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
            if finger == 'thumb':
                # 使用专门的拇指伸直检测方法
                finger_states[finger] = self.is_thumb_extended(landmarks)
            else:
                finger_states[finger] = self.is_finger_extended_simple(finger, landmarks)
        
        features['finger_states'] = finger_states
        
        # 计算伸直手指数量（包含拇指）
        extended_count = sum(1 for state in finger_states.values() if state)
        features['extended_count'] = extended_count
        
        # 计算伸直手指的组合
        extended_fingers = [finger for finger, state in finger_states.items() if state]
        features['extended_fingers'] = extended_fingers
        
        # 计算拇指位置相对其他手指的位置
        features['thumb_position'] = self.get_thumb_position(finger_tips, landmarks)
        
        # 调试信息
        print(f"手指状态: {finger_states}")
        print(f"伸直手指: {extended_fingers} (共{extended_count}个)")
        print(f"拇指位置: {features['thumb_position']}")
        
        return features
    
    def is_finger_extended_simple(self, finger: str, landmarks: List) -> bool:
        """简化的手指伸直检测（用于除拇指外的手指）"""
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
        
        # 获取指尖和指根坐标
        tip = landmarks[indices[-1]]  # 指尖
        base = landmarks[indices[0]]  # 指根
        
        # 计算指尖到指根的距离
        distance = ((tip[0] - base[0])**2 + (tip[1] - base[1])**2) ** 0.5
        
        # 返回伸直状态
        return distance > 0.08
    
    def is_thumb_extended(self, landmarks: List) -> bool:
        """专门的拇指伸直检测"""
        # 拇指的关键点（0: 手腕, 1: 拇指CMC, 2: 拇指MCP, 3: 拇指IP, 4: 拇指指尖）
        thumb_landmarks = [landmarks[i] for i in [2, 3, 4]]  # MCP, IP, 指尖
        
        # 方法1：计算拇指关键点之间的角度
        thumb_tip = np.array(thumb_landmarks[2][:2])  # 指尖
        thumb_ip = np.array(thumb_landmarks[1][:2])    # IP关节
        thumb_mcp = np.array(thumb_landmarks[0][:2])   # MCP关节
        
        # 计算两个向量
        vec1 = thumb_ip - thumb_mcp
        vec2 = thumb_tip - thumb_ip
        
        # 计算向量长度
        len_vec1 = np.linalg.norm(vec1)
        len_vec2 = np.linalg.norm(vec2)
        
        if len_vec1 == 0 or len_vec2 == 0:
            return False
        
        # 计算角度（弧度）
        dot_product = np.dot(vec1, vec2)
        angle = np.arccos(dot_product / (len_vec1 * len_vec2))
        
        # 将弧度转换为角度
        angle_degrees = np.degrees(angle)
        
        print(f"拇指角度: {angle_degrees:.1f}度")
        
        # 角度在160-180度之间表示拇指伸直（接近直线）
        # 角度较小表示拇指弯曲
        return angle_degrees > 140  # 比180度低一点，允许轻微弯曲
    
    def is_thumb_extended_alternative(self, landmarks: List) -> bool:
        """备选的拇指伸直检测方法：使用指尖到手掌的距离"""
        # 拇指指尖
        thumb_tip = np.array(landmarks[4][:2])
        
        # 手掌中心（使用手腕和部分手指根部计算）
        wrist = np.array(landmarks[0][:2])
        index_mcp = np.array(landmarks[5][:2])
        pinky_mcp = np.array(landmarks[17][:2])
        
        # 计算手掌中心
        palm_center = (wrist + index_mcp + pinky_mcp) / 3
        
        # 计算拇指指尖到手掌中心的距离
        distance = np.linalg.norm(thumb_tip - palm_center)
        
        print(f"拇指到手掌距离: {distance:.3f}")
        
        # 如果距离较大，说明拇指伸直；如果距离较小，说明拇指弯曲靠近手掌
        return distance > 0.2
    
    def get_thumb_position(self, finger_tips: Dict, landmarks: List) -> str:
        """获取拇指位置（相对于手掌）"""
        thumb_tip = finger_tips['thumb']
        wrist = landmarks[0]  # 手腕点
        
        # 计算拇指相对于手腕的位置
        thumb_x, thumb_y = thumb_tip
        wrist_x, wrist_y = wrist[0], wrist[1]
        
        # 计算水平方向的位置
        if thumb_x < wrist_x - 0.05:
            return 'left'  # 拇指在手腕左侧
        elif thumb_x > wrist_x + 0.05:
            return 'right'  # 拇指在手腕右侧
        else:
            return 'center'  # 拇指在手腕正上方/下方
    
    def recognize_chord_by_count_and_position(self, features: Dict, bbox: Dict) -> str:
        """基于手指数量和位置识别和弦"""
        extended_count = features['extended_count']
        hand_position = self.get_hand_position(bbox)
        thumb_position = features.get('thumb_position', 'center')
        
        print(f"调试信息: 伸直手指数={extended_count}, 位置={hand_position}, 拇指位置={thumb_position}")
        
        # 基于伸直手指数量和位置的识别
        # 0指伸直：没有手势
        if extended_count == 0:
            print("❌ 未识别: 没有伸直的手指")
            return "none"
        
        # 1指伸直：单音手势
        elif extended_count == 1 and hand_position == 'high':
            print("🎵 识别为 单音手势（高位）")
            return 'SINGLE_NOTE_HIGH'
        elif extended_count == 1 and hand_position == 'low':
            print("🎵 识别为 单音手势（低位）")
            return 'SINGLE_NOTE_LOW'
        
        # 2指伸直：C/G和弦
        elif extended_count == 2 and hand_position == 'high':
            print("✅ 识别为 C大调: 两指伸直 + 手部抬高")
            return 'C_major'
        
        elif extended_count == 2 and hand_position == 'low':
            print("✅ 识别为 G大调: 两指伸直 + 手部放低")
            return 'G_major'
        
        # 3指伸直：D/Am和弦
        elif extended_count == 3 and hand_position == 'high':
            print("✅ 识别为 D大调: 三指伸直 + 手部抬高")
            return 'D_major'
        
        elif extended_count == 3 and hand_position == 'low':
            print("✅ 识别为 A小调: 三指伸直 + 手部放低")
            return 'A_minor'
        
        # 4指伸直：Em/F和弦
        elif extended_count == 4 and hand_position == 'high':
            print("✅ 识别为 E小调: 四指伸直 + 手部抬高")
            return 'E_minor'
        
        elif extended_count == 4 and hand_position == 'low':
            print("✅ 识别为 F大调: 四指伸直 + 手部放低")
            return 'F_major'
        
        # 5指伸直：全指手势
        elif extended_count == 5:
            if hand_position == 'high':
                print("🌟 识别为 全指手势（高位）")
                return 'ALL_FINGERS_HIGH'
            elif hand_position == 'low':
                print("🌟 识别为 全指手势（低位）")
                return 'ALL_FINGERS_LOW'
            else:
                print("🌟 识别为 全指手势（中间）")
                return 'ALL_FINGERS_MID'
        
        # 特殊手势：拇指和其他手指组合
        elif features.get('finger_states', {}).get('thumb', False):
            # 如果拇指伸直，检查是否是特定的拇指手势
            extended_fingers = features.get('extended_fingers', [])
            if 'thumb' in extended_fingers and len(extended_fingers) == 2:
                if 'index' in extended_fingers:
                    if hand_position == 'high':
                        print("👍 识别为 拇指示意（高位）")
                        return 'THUMB_INDEX_HIGH'
                    else:
                        print("👍 识别为 拇指示意（低位）")
                        return 'THUMB_INDEX_LOW'
        
        print(f"❌ 未识别: 伸直{extended_count}指, 位置{hand_position}, 拇指位置{thumb_position}")
        return "unknown"
    
    def get_hand_position(self, bbox: Dict) -> str:
        """获取手部位置（高/中/低）"""
        vertical_center = (bbox['y_min'] + bbox['y_max']) / 2
        
        print(f"手部垂直位置: {vertical_center}")
        
        # 调整位置阈值
        if vertical_center < 0.45:  # 较高位置
            return 'high'
        elif vertical_center < 0.65:  # 中间位置
            return 'middle'
        else:  # 较低位置
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