import cv2
import mediapipe as mp
import numpy as np
import time

class AirGuitarGestureRecognizer:
    def __init__(self):
        """初始化MediaPipe手势识别器"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,  # 检测两只手
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # 手势状态
        self.left_hand_strings = []  # 左手选择的弦列表
        self.right_hand_fret = 0     # 右手选择的品
        self.volume = 0.5           # 音量 (0-1)
        
        # 控制状态
        self.is_recording = False   # 是否开始录制
        self.hand_positions = {}    # 存储手部位置用于检测上下移动
        
    def get_finger_state(self, landmarks, finger_tip_idx, finger_pip_idx, finger_mcp_idx, wrist_idx):
        """判断单个手指是否伸直"""
        tip = landmarks[finger_tip_idx]
        pip = landmarks[finger_pip_idx]
        mcp = landmarks[finger_mcp_idx]
        wrist = landmarks[wrist_idx]
        
        # 方法1: 计算指尖与指关节的距离比
        tip_to_wrist = np.linalg.norm(np.array([tip.x, tip.y]) - np.array([wrist.x, wrist.y]))
        pip_to_wrist = np.linalg.norm(np.array([pip.x, pip.y]) - np.array([wrist.x, wrist.y]))
        
        # 方法2: 检查指尖是否在指关节之上（针对竖向手势）
        # 图像坐标y轴向下，所以y值越小表示越高
        is_extended_by_y = tip.y < pip.y - 0.02
        
        # 方法3: 计算角度（更准确）
        # 使用三个点计算角度：MCP -> PIP -> TIP
        vector1 = np.array([pip.x - mcp.x, pip.y - mcp.y])
        vector2 = np.array([tip.x - pip.x, tip.y - pip.y])
        
        if np.linalg.norm(vector1) == 0 or np.linalg.norm(vector2) == 0:
            return False
            
        # 计算余弦值
        cos_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        
        # 角度小于160度通常表示弯曲
        is_extended_by_angle = angle > 155

        # 距离比约束：指尖到腕的距离应明显大于 pip 到腕的距离（避免近景误判）
        dist_ratio = tip_to_wrist / (pip_to_wrist + 1e-6)

        # 对拇指采用专用判定：拇指的伸展通常沿掌宽方向
        if finger_tip_idx == 4:
            try:
                index_mcp = landmarks[5]
                pinky_mcp = landmarks[17]
                palm_width_vec = np.array([pinky_mcp.x - index_mcp.x, pinky_mcp.y - index_mcp.y])
                pw_norm = np.linalg.norm(palm_width_vec)
                if pw_norm > 1e-6:
                    palm_width_unit = palm_width_vec / pw_norm
                else:
                    palm_width_unit = np.array([1.0, 0.0])

                tip_vec = np.array([tip.x - wrist.x, tip.y - wrist.y])
                ip_vec = np.array([pip.x - wrist.x, pip.y - wrist.y])
                proj_tip = np.dot(tip_vec, palm_width_unit)
                proj_ip = np.dot(ip_vec, palm_width_unit)
                # MCP 到腕的距离用于辅助判断，避免近景或噪声导致的误判
                mcp_to_wrist = np.linalg.norm(np.array([mcp.x - wrist.x, mcp.y - wrist.y]))
                # 更严格的组合条件：要求投影差显著且指尖比 MCP 更远，或角度与距离比同时满足
                proj_diff = abs(proj_tip) - abs(proj_ip)
                cond_proj = proj_diff > 0.03 and dist_ratio > 0.8 and (tip_to_wrist > mcp_to_wrist * 0.9)
                cond_angle = is_extended_by_angle and dist_ratio > 0.75
                thumb_ok = bool(cond_proj or cond_angle)
            except Exception:
                thumb_ok = (is_extended_by_angle or is_extended_by_y) and (dist_ratio > 0.7)

            return bool(thumb_ok)

        # 对无名指放宽距离比阈值，提升在某些角度下的识别率
        if finger_tip_idx == 16:
            dist_thresh = 0.75
        else:
            dist_thresh = 0.85

        # 综合判断：允许角度或高度成立，同时满足一定的距离比
        is_extended = (is_extended_by_angle or is_extended_by_y) and (dist_ratio > dist_thresh)

        return bool(is_extended)
    
    def detect_left_hand_strings(self, landmarks):
        """检测左手手势，返回选择的弦列表"""
        strings = []
        
        # MediaPipe手部关键点索引
        # 拇指: 4(指尖), 3(第二关节), 2(第一关节), 1(根部)
        # 食指: 8(指尖), 7(第三关节), 6(第二关节), 5(根部)
        # 中指: 12(指尖), 11(第三关节), 10(第二关节), 9(根部)
        # 无名指: 16(指尖), 15(第三关节), 14(第二关节), 13(根部)
        # 小指: 20(指尖), 19(第三关节), 18(第二关节), 17(根部)
        
        # 检查每个手指是否伸直
        thumb_extended = self.get_finger_state(landmarks, 4, 3, 2, 0)
        index_extended = self.get_finger_state(landmarks, 8, 7, 6, 0)
        middle_extended = self.get_finger_state(landmarks, 12, 11, 10, 0)
        ring_extended = self.get_finger_state(landmarks, 16, 15, 14, 0)
        pinky_extended = self.get_finger_state(landmarks, 20, 19, 18, 0)
        
        # 判断是否是握拳（第6弦）
        # 握拳：所有手指都不伸直
        if not (thumb_extended or index_extended or middle_extended or ring_extended or pinky_extended):
            strings.append(6)
        else:
            # 添加伸直手指对应的弦
            if thumb_extended:
                strings.append(1)
            if index_extended:
                strings.append(2)
            if middle_extended:
                strings.append(3)
            if ring_extended:
                strings.append(4)
            if pinky_extended:
                strings.append(5)
        
        return strings
    
    def get_palm_orientation(self, landmarks):
        """判断手掌朝向：竖向或横向"""
        # 获取关键点
        wrist = landmarks[0]
        index_mcp = landmarks[5]  # 食指根部
        pinky_mcp = landmarks[17] # 小指根部
        
        # 计算手掌宽度向量
        palm_vector = np.array([pinky_mcp.x - index_mcp.x, pinky_mcp.y - index_mcp.y])
        
        # 计算与水平线的夹角
        angle = np.degrees(np.arctan2(abs(palm_vector[1]), abs(palm_vector[0])))
        
        # 如果夹角大于45度，认为是竖向；否则是横向
        if angle > 45:
            return "vertical"
        else:
            return "horizontal"
    
    def detect_right_hand_fret(self, landmarks):
        """检测右手手势，返回选择的品"""
        # 先检查是否是握拳（开始手势）
        thumb_extended = self.get_finger_state(landmarks, 4, 3, 2, 0)
        index_extended = self.get_finger_state(landmarks, 8, 7, 6, 0)
        middle_extended = self.get_finger_state(landmarks, 12, 11, 10, 0)
        ring_extended = self.get_finger_state(landmarks, 16, 15, 14, 0)
        pinky_extended = self.get_finger_state(landmarks, 20, 19, 18, 0)
        
        # 获取手掌朝向
        orientation = self.get_palm_orientation(landmarks)
        
        # 计算伸直的手指数
        extended_fingers = []
        if thumb_extended:
            extended_fingers.append("thumb")
        if index_extended:
            extended_fingers.append("index")
        if middle_extended:
            extended_fingers.append("middle")
        if ring_extended:
            extended_fingers.append("ring")
        if pinky_extended:
            extended_fingers.append("pinky")
        
        finger_count = len(extended_fingers)
        
        # 根据你的设计规则确定品
        if orientation == "vertical":
            if finger_count == 1:
                # 单个手指：1-5品
                return finger_count
            elif finger_count == 2:
                # 特殊组合
                if "thumb" in extended_fingers and "index" in extended_fingers:
                    return 11  # 拇指+食指
                elif "thumb" in extended_fingers and "pinky" in extended_fingers:
                    return 12  # 拇指+小指
                elif "index" in extended_fingers and "middle" in extended_fingers:
                    return 13  # 食指+中指
                elif "index" in extended_fingers and "pinky" in extended_fingers:
                    return 14  # 食指+小指
                else:
                    return finger_count  # 默认按手指数
            elif 2 <= finger_count <= 5:
                return finger_count
        elif orientation == "horizontal":
            if 1 <= finger_count <= 5:
                return finger_count + 5  # 6-10品
        
        # 如果没有匹配，返回0品
        return 0
    
    def detect_control_gestures(self, results, frame_shape):
        """检测控制手势"""
        control_action = None
        
        if results.multi_hand_landmarks and results.multi_handedness:
            right_fist = False
            left_fist = False
            
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_label = results.multi_handedness[idx].classification[0].label
                
                # 检查是否是握拳
                thumb_extended = self.get_finger_state(hand_landmarks.landmark, 4, 3, 2, 0)
                index_extended = self.get_finger_state(hand_landmarks.landmark, 8, 7, 6, 0)
                middle_extended = self.get_finger_state(hand_landmarks.landmark, 12, 11, 10, 0)
                ring_extended = self.get_finger_state(hand_landmarks.landmark, 16, 15, 14, 0)
                pinky_extended = self.get_finger_state(hand_landmarks.landmark, 20, 19, 18, 0)
                
                is_fist = not (thumb_extended or index_extended or middle_extended or ring_extended or pinky_extended)
                
                # 获取手腕位置
                wrist = hand_landmarks.landmark[0]
                wrist_y = wrist.y * frame_shape[0]
                
                # 存储手部位置用于检测上下移动
                if hand_label == "Left":
                    if "left" not in self.hand_positions:
                        self.hand_positions["left"] = []
                    self.hand_positions["left"].append(wrist_y)
                    if len(self.hand_positions["left"]) > 10:
                        self.hand_positions["left"].pop(0)
                    
                    left_fist = is_fist
                else:  # Right hand
                    if "right" not in self.hand_positions:
                        self.hand_positions["right"] = []
                    self.hand_positions["right"].append(wrist_y)
                    if len(self.hand_positions["right"]) > 10:
                        self.hand_positions["right"].pop(0)
                    
                    right_fist = is_fist
                    
                    # 检测手部上下移动（音量控制）
                    if len(self.hand_positions["right"]) >= 5:
                        # 计算最近5个位置的平均变化
                        positions = self.hand_positions["right"][-5:]
                        if len(positions) >= 2:
                            change = positions[-1] - positions[0]
                            
                            # 如果手部持续上升或下降
                            if change < -20:  # 上升（y值减小）
                                control_action = "volume_up"
                            elif change > 20:  # 下降（y值增加）
                                control_action = "volume_down"
            
            # 检测开始/结束手势
            if right_fist and not left_fist:
                control_action = "start"
            elif right_fist and left_fist:
                control_action = "end"
        
        return control_action
    
    def process_frame(self, frame):
        """处理一帧图像，返回识别结果"""
        # 转换颜色空间
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        
        # 处理图像
        results = self.hands.process(image_rgb)
        
        # 转换回来
        image_rgb.flags.writeable = True
        output_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        
        # 重置手势状态
        self.left_hand_strings = []
        self.right_hand_fret = 0
        
        # 检测控制手势
        control_action = self.detect_control_gestures(results, frame.shape)
        
        # 处理控制动作
        if control_action:
            if control_action == "start":
                self.is_recording = True
                print("🎸 开始演奏!")
            elif control_action == "end":
                self.is_recording = False
                print("🎸 结束演奏!")
            elif control_action == "volume_up":
                self.volume = min(1.0, self.volume + 0.05)
                print(f"🔊 音量增加: {self.volume:.2f}")
            elif control_action == "volume_down":
                self.volume = max(0.0, self.volume - 0.05)
                print(f"🔊 音量减小: {self.volume:.2f}")
        
        # 只有当开始后，才检测演奏手势
        if self.is_recording and results.multi_hand_landmarks and results.multi_handedness:
            left_detected = False
            right_detected = False
            
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_label = results.multi_handedness[idx].classification[0].label
                
                # 绘制手部关键点
                self.mp_drawing.draw_landmarks(
                    output_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
                
                # 区分左右手并识别手势
                if hand_label == "Left":
                    self.left_hand_strings = self.detect_left_hand_strings(hand_landmarks.landmark)
                    left_detected = True
                    
                    # 在画面中显示左手选择的弦
                    cv2.putText(output_frame, f"左手弦: {self.left_hand_strings}", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                else:  # Right hand
                    # 检查是否是握拳（控制手势已在前面处理）
                    thumb_extended = self.get_finger_state(hand_landmarks.landmark, 4, 3, 2, 0)
                    index_extended = self.get_finger_state(hand_landmarks.landmark, 8, 7, 6, 0)
                    middle_extended = self.get_finger_state(hand_landmarks.landmark, 12, 11, 10, 0)
                    is_fist = not (thumb_extended or index_extended or middle_extended)
                    
                    if not is_fist:  # 不是握拳才检测品
                        self.right_hand_fret = self.detect_right_hand_fret(hand_landmarks.landmark)
                        right_detected = True
                        
                        # 在画面中显示右手选择的品
                        cv2.putText(output_frame, f"右手品: {self.right_hand_fret}", 
                                  (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 如果左右手都检测到，显示和弦信息
            if left_detected and right_detected and self.left_hand_strings:
                chord_info = f"和弦: 弦{self.left_hand_strings}, 品{self.right_hand_fret}"
                cv2.putText(output_frame, chord_info, 
                          (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # 这里可以添加播放和弦的代码
                self.play_chord(self.left_hand_strings, self.right_hand_fret)
        
        # 显示状态信息
        status = "录制中" if self.is_recording else "等待开始"
        cv2.putText(output_frame, f"状态: {status}", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(output_frame, f"音量: {self.volume:.2f}", 
                   (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return output_frame, self.left_hand_strings, self.right_hand_fret
    
    def play_chord(self, strings, fret):
        """播放和弦（这里需要你实现音频播放逻辑）"""
        # 这里只是一个示例，你需要根据你的音频库来实现
        print(f"🎵 播放和弦: 弦{strings}, 品{fret}, 音量{self.volume}")
        
        # 根据弦和品计算音高
        # 吉他标准调音：EADGBE (从6弦到1弦)
        standard_tuning = [40, 45, 50, 55, 59, 64]  # MIDI音符编号
        
        notes = []
        for string in strings:
            if 1 <= string <= 6:
                # 计算该弦在指定品的音高
                midi_note = standard_tuning[string-1] + fret
                notes.append(midi_note)
        
        # 在这里调用你的音频播放函数
        # 例如: play_notes(notes, self.volume)
        
    def run(self):
        """运行主循环"""
        cap = cv2.VideoCapture(0)
        
        print("🎸 空气吉他系统启动!")
        print("控制手势:")
        print("  - 右手握拳: 开始")
        print("  - 双手握拳: 结束")
        print("  - 手缓慢上升: 加大音量")
        print("  - 手缓慢下降: 降低音量")
        print("\n演奏手势:")
        print("  - 左手: 手指伸直选择弦 (拇指=1弦, 食指=2弦, 中指=3弦, 无名指=4弦, 小指=5弦, 握拳=6弦)")
        print("  - 右手: 竖向1-5指=1-5品, 横向1-5指=6-10品")
        print("          特殊手势: 拇指+食指=11品, 拇指+小指=12品, 食指+中指=13品, 食指+小指=14品")
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("无法读取摄像头")
                break
            
            # 处理帧
            output_frame, strings, fret = self.process_frame(frame)
            
            # 显示结果
            cv2.imshow('Air Guitar', output_frame)
            
            # 按ESC退出
            if cv2.waitKey(5) & 0xFF == 27:
                break
        
        cap.release()
        cv2.destroyAllWindows()

# 该文件只导出 `AirGuitarGestureRecognizer` 类供主程序调用。
# 若需要独立运行调试，请使用项目提供的 `debug_hand_test.py` 或直接运行 `main_app.py`。