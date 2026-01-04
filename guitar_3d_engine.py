import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
from typing import List, Dict, Tuple
import utils

class Particle:
    """粒子类"""
    def __init__(self, position: List[float], velocity: List[float], 
                 color: List[float], lifetime: float):
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
    def update(self, delta_time: float):
        """更新粒子状态"""
        self.position += self.velocity * delta_time
        self.lifetime -= delta_time
        
        # 颜色随生命周期变化
        alpha = self.lifetime / self.max_lifetime
        self.color[3] = alpha
        
    def is_alive(self) -> bool:
        """检查粒子是否存活"""
        return self.lifetime > 0

class Guitar3DEngine:
    """3D吉他引擎"""
    
    def __init__(self, config: Dict = None):
        if config is None:
            config = utils.load_config()['rendering']
            
        self.config = config
        self.particles = []
        self.guitar_rotation = [0, 0, 0]
        self.guitar_position = [0, -1, -5]
        self.string_vibration = [0] * 6
        
        # 初始化GLUT（必需）
        glutInit()
        self.setup_opengl()
        self.load_textures()
    
    def setup_opengl(self):
        """设置OpenGL"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # 设置光源
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
        
        glClearColor(*self.config['background_color'])
    
    def load_textures(self):
        """加载纹理（简化实现）"""
        self.textures = {}
        # 实际实现中这里会加载粒子纹理
    
    def render_guitar(self):
        """渲染吉他模型"""
        glPushMatrix()
        glTranslatef(*self.guitar_position)
        glRotatef(self.guitar_rotation[0], 1, 0, 0)
        glRotatef(self.guitar_rotation[1], 0, 1, 0)
        glRotatef(self.guitar_rotation[2], 0, 0, 1)
        
        # 渲染吉他主体
        self.render_guitar_body()
        
        # 渲染琴颈和指板
        self.render_guitar_neck()
        
        # 渲染弦
        self.render_strings()
        
        glPopMatrix()
    
    def render_guitar_body(self):
        """渲染吉他主体"""
        glColor3f(0.3, 0.2, 0.1)  # 木色
        
        # 简化的吉他主体（实际实现中会加载3D模型）
        glBegin(GL_QUADS)
        # 吉他主体前面
        glVertex3f(-1.5, -0.5, 0)
        glVertex3f(1.5, -0.5, 0)
        glVertex3f(1.5, 0.5, 0)
        glVertex3f(-1.5, 0.5, 0)
        glEnd()
    
    def render_guitar_neck(self):
        """渲染吉他琴颈"""
        glColor3f(0.2, 0.15, 0.1)
        
        glPushMatrix()
        glTranslatef(0, 0.5, 0)
        
        # 琴颈
        glBegin(GL_QUADS)
        glVertex3f(-0.1, 0, 0)
        glVertex3f(0.1, 0, 0)
        glVertex3f(0.1, 2, 0)
        glVertex3f(-0.1, 2, 0)
        glEnd()
        
        # 品丝
        glColor3f(0.8, 0.8, 0.8)
        for i in range(1, 21):
            y_pos = i * 0.1
            glBegin(GL_LINES)
            glVertex3f(-0.15, y_pos, 0)
            glVertex3f(0.15, y_pos, 0)
            glEnd()
        
        glPopMatrix()
    
    def render_strings(self):
        """渲染吉他弦"""
        string_colors = [
            [1, 0, 0],    # E2 - 红色
            [1, 0.5, 0],  # A - 橙色
            [1, 1, 0],    # D - 黄色
            [0, 1, 0],    # G - 绿色
            [0, 0, 1],    # B - 蓝色
            [0.5, 0, 0.5] # E4 - 紫色
        ]
        
        for i in range(6):
            x_pos = -0.12 + i * 0.04
            glColor3f(*string_colors[i])
            
            # 添加弦振动效果
            vibration = np.sin(pygame.time.get_ticks() * 0.01 + i) * self.string_vibration[i] * 0.1
            
            glBegin(GL_LINE_STRIP)
            for j in range(21):
                y_pos = j * 0.1
                # 简化的弦振动效果
                z_offset = vibration * np.sin(y_pos * np.pi / 2)
                glVertex3f(x_pos, y_pos, z_offset)
            glEnd()
    
    def create_particles(self, position: List[float], count: int = 10):
        """创建粒子效果"""
        for _ in range(count):
            velocity = [
                np.random.uniform(-1, 1),
                np.random.uniform(0, 2),
                np.random.uniform(-1, 1)
            ]
            color = [
                np.random.uniform(0.5, 1),
                np.random.uniform(0.5, 1),
                np.random.uniform(0.5, 1),
                1.0
            ]
            lifetime = np.random.uniform(1, 3)
            
            self.particles.append(Particle(position, velocity, color, lifetime))
    
    def update_particles(self, delta_time: float):
        """更新所有粒子"""
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update(delta_time)
    
    def render_particles(self):
        """渲染所有粒子"""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        
        for particle in self.particles:
            glPushMatrix()
            glTranslatef(*particle.position)
            glColor4f(*particle.color)
            
            # 渲染粒子为小四边形
            size = 0.1
            glBegin(GL_QUADS)
            glVertex3f(-size, -size, 0)
            glVertex3f(size, -size, 0)
            glVertex3f(size, size, 0)
            glVertex3f(-size, size, 0)
            glEnd()
            
            glPopMatrix()
        
        glEnable(GL_LIGHTING)
    
    def trigger_string_vibration(self, string_index: int):
        """触发弦振动"""
        self.string_vibration[string_index] = 1.0
        # 在弦的位置创建粒子
        x_pos = -0.12 + string_index * 0.04
        self.create_particles([x_pos, 1.0, 0], 20)
    
    def update_string_vibration(self, delta_time: float):
        """更新弦振动"""
        for i in range(len(self.string_vibration)):
            if self.string_vibration[i] > 0:
                self.string_vibration[i] -= delta_time * 2
                self.string_vibration[i] = max(0, self.string_vibration[i])
    
    def render(self, delta_time: float):
        """主渲染函数"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # 设置相机
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)
        
        # 更新和渲染
        self.update_particles(delta_time)
        self.update_string_vibration(delta_time)
        
        self.render_guitar()
        self.render_particles()
        
        pygame.display.flip()
