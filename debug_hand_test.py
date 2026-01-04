import cv2
from hand_tracker import HandTracker
import utils

def main():
    config = utils.load_config()['hand_tracking']
    ht = HandTracker(config)
    cap = cv2.VideoCapture(0)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            proc, hands = ht.process_frame(frame)
            for h in hands:
                fs = h.get('finger_states', {})
                # 若加载了 MediaPipe Gesture Recognizer，则尝试通过模型获取标签
                mp_label = ''
                if getattr(ht, 'gesture_model_loaded', False):
                    mp_label = ht._recognize_with_media_pipe(proc, h.get('world_landmarks'))
                gesture = ht.get_hand_gesture(h)
                print(f"Hand type: {h.get('type')} | gesture: {gesture} | mp_label: {mp_label} | finger_states: {fs}")
            cv2.imshow('Debug Hand Test', proc)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        # 捕获 Ctrl+C，优雅退出
        print("Interrupted by user (KeyboardInterrupt). Exiting...")
    finally:
        # 在释放资源时也捕获可能的中断，保证清理完成
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            ht.release()
        except Exception:
            pass

if __name__ == '__main__':
    main()
