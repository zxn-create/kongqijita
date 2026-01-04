import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Dict, Any
import utils

class HandTracker:
    """手部关键点检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = utils.load_config()['hand_tracking']
            
        self.config = config
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            model_complexity=config['model_complexity'],
            min_detection_confidence=config['min_detection_confidence'],
            min_tracking_confidence=config['min_tracking_confidence'],
            max_num_hands=config['max_num_hands']
        )
        
    def process_frame(self, image: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """处理帧并检测手部关键点"""
        results = self.hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        hand_data = []
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # 提取关键点坐标
                landmarks = []
                for landmark in hand_landmarks.landmark:
                    landmarks.append((landmark.x, landmark.y, landmark.z))
                
                # 获取手型（左手/右手）
                hand_type = handedness.classification[0].label
                
                hand_data.append({
                    'landmarks': landmarks,
                    'type': hand_type,
                    'world_landmarks': hand_landmarks.landmark
                })
                
                # 绘制关键点
                self.mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        
        return image, hand_data
    
    def get_finger_positions(self, hand_data: Dict) -> Dict[str, Tuple[float, float]]:
        """获取手指尖端位置"""
        if not hand_data:
            return {}
            
        landmarks = hand_data['landmarks']
        finger_tips = {
            'thumb': landmarks[4],
            'index': landmarks[8],
            'middle': landmarks[12],
            'ring': landmarks[16],
            'pinky': landmarks[20]
        }
        
        return finger_tips
    
    def is_finger_extended(self, landmarks: List[Tuple[float, float, float]], finger_tip: int, 
                          finger_joints: List[int]) -> bool:
        """判断手指是否伸直"""
        tip = landmarks[finger_tip]
        joints = [landmarks[joint] for joint in finger_joints]
        
        # 计算手指方向向量
        finger_vector = np.array([tip[0] - joints[0][0], tip[1] - joints[0][1]])
        finger_length = np.linalg.norm(finger_vector)
        
        if finger_length < 0.05:  # 阈值，可根据需要调整
            return False
            
        return True
    
    def get_hand_gesture(self, hand_data: Dict) -> str:
        """识别手势"""
        if not hand_data:
            return "none"
            
        landmarks = hand_data['landmarks']
        finger_tips = self.get_finger_positions(hand_data)
        
        # 简单的拳头检测
        thumb_tip = np.array(finger_tips['thumb'][:2])
        index_tip = np.array(finger_tips['index'][:2])
        middle_tip = np.array(finger_tips['middle'][:2])
        
        dist_thumb_index = np.linalg.norm(thumb_tip - index_tip)
        dist_thumb_middle = np.linalg.norm(thumb_tip - middle_tip)
        
        if dist_thumb_index < 0.05 and dist_thumb_middle < 0.05:
            return "fist"
        else:
            return "open"
    
    def release(self):
        """释放资源"""
        self.hands.close()
