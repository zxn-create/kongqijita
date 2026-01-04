import pygame
import time
import os

pygame.mixer.init(frequency=44100)
path = os.path.join('assets', 'guitar_samples', 'single_notes', 'string1_fret0.wav')
print('尝试播放:', path)
if not os.path.exists(path):
    print('文件不存在:', path)
else:
    snd = pygame.mixer.Sound(path)
    snd.set_volume(0.8)
    ch = snd.play()
    time.sleep(1.2)
    print('播放完成')
    try:
        ch.stop()
    except Exception:
        pass
pygame.mixer.quit()
