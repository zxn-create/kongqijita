import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Dict, Any
import utils
import os
import logging



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

        # 可选：MediaPipe Tasks 手势识别器（需在 config 中设置 'use_gesture_recognizer' 和 'gesture_model_path'）
        self.gesture_recognizer = None
        self.gesture_model_loaded = False
        try:
            gp = config.get('use_gesture_recognizer', False)
            model_path = config.get('gesture_model_path')
        except Exception:
            gp = False
            model_path = None

        if gp and model_path:
            try:
                # 尝试导入 MediaPipe Tasks（若可用）并延迟加载模型
                from mediapipe.tasks.python import vision as mp_vision
                if os.path.exists(model_path):
                    # HandGestureRecognizer API 可能因 mediapipe 版本而不同，这里尝试常见模式
                    try:
                        self.gesture_recognizer = mp_vision.HandGestureRecognizer.create_from_model_path(model_path)
                    except Exception:
                        try:
                            self.gesture_recognizer = mp_vision.HandLandmarker.create_from_model_path(model_path)
                        except Exception:
                            self.gesture_recognizer = None

                    if self.gesture_recognizer is not None:
                        self.gesture_model_loaded = True
                        logging.info(f"Loaded gesture recognizer model: {model_path}")
                    else:
                        logging.warning("无法创建手势识别器实例，回退到关键点投影方法。")
                else:
                    logging.warning(f"手势识别模型文件未找到: {model_path}")
            except Exception as e:
                logging.warning(f"MediaPipe Tasks 不可用或加载失败: {e}")
        # 实例化提供的手势识别实现，用于更精确的指尖/角度检测
        try:
            # 动态导入用户提供的 hand.py，以避免在模块导入时出现循环或依赖导致的问题
            try:
                from hand import AirGuitarGestureRecognizer
            except Exception:
                AirGuitarGestureRecognizer = None

            if AirGuitarGestureRecognizer is not None:
                try:
                    self.external_recognizer = AirGuitarGestureRecognizer()
                except Exception:
                    self.external_recognizer = None
            else:
                self.external_recognizer = None
        except Exception:
            self.external_recognizer = None
        
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
                
                # 生成基于 world_landmarks 的更稳健的 finger_states（使用外部实现）
                finger_states = {}
                try:
                    if self.external_recognizer is not None:
                        lm = hand_landmarks.landmark
                        # 使用外部实现的 get_finger_state，传入 Landmark 列表
                        thumb = self.external_recognizer.get_finger_state(lm, 4, 3, 2, 0)
                        index = self.external_recognizer.get_finger_state(lm, 8, 7, 6, 0)
                        middle = self.external_recognizer.get_finger_state(lm, 12, 11, 10, 0)
                        ring = self.external_recognizer.get_finger_state(lm, 16, 15, 14, 0)
                        pinky = self.external_recognizer.get_finger_state(lm, 20, 19, 18, 0)
                        finger_states = {
                            'thumb': bool(thumb),
                            'index': bool(index),
                            'middle': bool(middle),
                            'ring': bool(ring),
                            'pinky': bool(pinky)
                        }
                except Exception:
                    finger_states = self.detect_fingers_extended(landmarks, hand_type)

                hand_data.append({
                    'landmarks': landmarks,
                    'type': hand_type,
                    'world_landmarks': hand_landmarks.landmark,
                    'finger_states': finger_states
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

    def detect_fingers_extended(self, landmarks: List[Tuple[float, float, float]], hand_type: str) -> Dict[str, bool]:
        """更稳健的手指伸展检测：基于沿掌方向的投影（对食指/中指/无名指/小指）和沿掌宽度的投影（对拇指）。

        landmarks: 列表，每项 (x,y,z)（归一化坐标）
        hand_type: 'Left' 或 'Right'
        返回: 字典，键为手指名，值为是否伸出
        """
        if not landmarks:
            return {}

        # 索引点
        idx = {
            'wrist': 0,
            'thumb_mcp': 2, 'thumb_ip': 3, 'thumb_tip': 4,
            'index_mcp': 5, 'index_pip': 6, 'index_tip': 8,
            'middle_mcp': 9, 'middle_pip': 10, 'middle_tip': 12,
            'ring_mcp': 13, 'ring_pip': 14, 'ring_tip': 16,
            'pinky_mcp': 17, 'pinky_pip': 18, 'pinky_tip': 20
        }

        arr = np.array(landmarks)
        wrist = arr[idx['wrist']]

        # 掌方向：用 middle_mcp - wrist
        palm_dir = arr[idx['middle_mcp']] - wrist
        palm_norm = np.linalg.norm(palm_dir)
        if palm_norm < 1e-6:
            palm_dir = np.array([0.0, -1.0, 0.0])
        else:
            palm_dir = palm_dir / palm_norm

        # 掌宽方向：index_mcp -> pinky_mcp
        palm_width = arr[idx['index_mcp']] - arr[idx['pinky_mcp']]
        pw_norm = np.linalg.norm(palm_width)
        if pw_norm < 1e-6:
            palm_width = np.array([1.0, 0.0, 0.0])
        else:
            palm_width = palm_width / pw_norm

        fingers = {}

        # 对于四指（食指/中指/无名指/小指），使用沿 palm_dir 的投影比较 tip 与 pip
        for name, tip_i, pip_i in [
            ('index', idx['index_tip'], idx['index_pip']),
            ('middle', idx['middle_tip'], idx['middle_pip']),
            ('ring', idx['ring_tip'], idx['ring_pip']),
            ('pinky', idx['pinky_tip'], idx['pinky_pip'])
        ]:
            tip = arr[tip_i]
            pip = arr[pip_i]
            proj_tip = np.dot(tip - wrist, palm_dir)
            proj_pip = np.dot(pip - wrist, palm_dir)
            # 阈值在归一化坐标下经验值，可按需调整
            fingers[name] = bool(proj_tip > proj_pip + 0.02)

        # 拇指：使用掌宽方向的投影（拇指伸出通常沿掌宽方向）
        thumb_tip = arr[idx['thumb_tip']]
        thumb_ip = arr[idx['thumb_ip']]
        proj_thumb = np.dot(thumb_tip - wrist, palm_width)
        proj_thumb_ip = np.dot(thumb_ip - wrist, palm_width)
        # 对左右手的方向不做显式符号判断，使用绝对增量判断是否明显伸出
        fingers['thumb'] = bool(abs(proj_thumb) > abs(proj_thumb_ip) + 0.015)

        return fingers

    def _recognize_with_media_pipe(self, image: np.ndarray, hand_landmarks) -> str:
        """若成功加载 MediaPipe Tasks 的手势识别器，则尝试使用其返回标签。否则返回空字符串表示未识别。"""
        if not self.gesture_model_loaded or self.gesture_recognizer is None:
            return ''
        try:
            # 尝试常见的方法调用接口；不同版本 API 可能差异较大，故作多分支保护
            try:
                # 假设 recognizer 有 recognize 或 detect 接口
                if hasattr(self.gesture_recognizer, 'recognize'):
                    result = self.gesture_recognizer.recognize(image)
                elif hasattr(self.gesture_recognizer, 'detect'):
                    result = self.gesture_recognizer.detect(image)
                else:
                    result = None
            except Exception:
                result = None

            if not result:
                return ''

            # 解析可能的结果结构
            # 兼容多种潜在返回结果，查找 label/text 字段
            if isinstance(result, list) or hasattr(result, '__iter__'):
                first = result[0]
            else:
                first = result

            # 尝试多种字段名
            label = ''
            for key in ('label', 'category_name', 'display_name', 'class_name', 'score'):
                if hasattr(first, key):
                    val = getattr(first, key)
                    if isinstance(val, str) and val:
                        label = val
                        break
                elif isinstance(first, dict) and key in first:
                    label = first[key]
                    break

            # 最后尝试将对象转为字符串
            if not label:
                label = str(first)

            return label
        except Exception:
            return ''
    
    def get_hand_gesture(self, hand_data: Dict) -> str:
        """识别手势"""
        if not hand_data:
            return "none"
            
        # 优先使用预计算的 finger_states（由 process_frame 使用外部实现计算）
        finger_states = hand_data.get('finger_states')
        if not finger_states:
            landmarks = hand_data.get('landmarks', [])
            hand_type = hand_data.get('type', 'Unknown')
            finger_states = self.detect_fingers_extended(landmarks, hand_type)
            hand_data['finger_states'] = finger_states

        count = sum(1 for v in finger_states.values() if v)

        if count == 0:
            return 'fist'
        if count == 5:
            return 'open'
        return f'extended_{count}'
    
    def release(self):
        """释放资源"""
        self.hands.close()
