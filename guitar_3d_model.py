# guitar_3d_model.py
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from typing import List, Tuple, Dict, Optional
import json

class Guitar3DModel:
    """完整的吉他3D建模类"""
    
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        
        # 初始化Pygame和OpenGL
        pygame.init()
        pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF)
        
        # OpenGL设置
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # 设置光源
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 5.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        
        # 材质设置
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)
        
        # 设置透视
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, width/height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        
        # 吉他参数
        self.guitar_rotation = [15, -30, 0]  # 旋转角度 (x, y, z)
        self.guitar_position = [0, -0.5, -5]  # 位置 (x, y, z)
        self.string_vibration = [0.0] * 6  # 6根弦的振动状态
        self.string_tension = [1.0] * 6  # 弦的张力
        
        # 颜色定义
        self.colors = {
            'mahogany': [0.4, 0.2, 0.1, 1.0],  # 桃花心木（琴身）
            'rosewood': [0.3, 0.15, 0.08, 1.0],  # 玫瑰木（指板）
            'maple': [0.9, 0.8, 0.6, 1.0],  # 枫木（琴颈）
            'ebony': [0.1, 0.1, 0.1, 1.0],  # 乌木（琴桥）
            'ivoroid': [0.95, 0.95, 0.9, 1.0],  # 象牙白（包边）
            'nickel': [0.8, 0.8, 0.8, 1.0],  # 镍（品丝、调音钮）
            'plastic_white': [1.0, 1.0, 1.0, 1.0],  # 塑料白（弦枕）
            'string_colors': [
                [0.9, 0.9, 0.9, 1.0],  # E4 - 银色
                [0.9, 0.9, 0.9, 1.0],  # B - 银色
                [0.9, 0.9, 0.9, 1.0],  # G - 银色
                [0.9, 0.9, 0.9, 1.0],  # D - 银色
                [0.9, 0.9, 0.9, 1.0],  # A - 银色
                [0.9, 0.9, 0.9, 1.0],  # E2 - 银色
            ]
        }
        
        # 动画参数
        self.animation_time = 0.0
        self.string_plucked = [False] * 6
        self.vibration_decay = 0.95
        
    def draw_sphere(self, radius, slices=20, stacks=20):
        """绘制球体"""
        quad = gluNewQuadric()
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)
    
    def draw_cylinder(self, radius, height, slices=20):
        """绘制圆柱体"""
        quad = gluNewQuadric()
        gluCylinder(quad, radius, radius, height, slices, 1)
        gluDeleteQuadric(quad)
    
    def draw_cube(self, size):
        """绘制立方体"""
        s = size / 2.0
        vertices = [
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
            [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]
        ]
        
        faces = [
            [0, 1, 2, 3],  # 后面
            [5, 4, 7, 6],  # 前面
            [4, 0, 3, 7],  # 左面
            [1, 5, 6, 2],  # 右面
            [3, 2, 6, 7],  # 上面
            [4, 5, 1, 0]   # 下面
        ]
        
        glBegin(GL_QUADS)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
    
    def draw_disk(self, inner_radius, outer_radius, slices=30):
        """绘制圆环"""
        quad = gluNewQuadric()
        gluDisk(quad, inner_radius, outer_radius, slices, 1)
        gluDeleteQuadric(quad)
    
    def draw_guitar_body(self):
        """绘制吉他琴身（基于真实吉他形状）"""
        glColor4f(*self.colors['mahogany'])
        
        # 琴身主体（简化形状）
        glPushMatrix()
        glScalef(2.5, 0.8, 0.5)
        self.draw_sphere(0.8, 30, 20)
        glPopMatrix()
        
        # 音孔
        glColor4f(*self.colors['ebony'])
        glPushMatrix()
        glTranslatef(0, 0, 0.26)
        self.draw_disk(0.08, 0.15, 30)
        glPopMatrix()
        
        # 包边
        glColor4f(*self.colors['ivoroid'])
        glPushMatrix()
        glTranslatef(0, 0, 0.25)
        self.draw_disk(0.78, 0.8, 50)
        glPopMatrix()
        
        # 琴桥
        glColor4f(*self.colors['ebony'])
        glPushMatrix()
        glTranslatef(0, -0.6, 0.15)
        glScalef(0.4, 0.05, 0.1)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 弦钉（6个）
        glColor4f(*self.colors['nickel'])
        for i in range(6):
            x_pos = -0.15 + i * 0.06
            glPushMatrix()
            glTranslatef(x_pos, -0.6, 0.15)
            self.draw_sphere(0.01, 10, 10)
            glPopMatrix()
    
    def draw_guitar_neck(self):
        """绘制吉他琴颈"""
        # 琴颈主体
        glColor4f(*self.colors['maple'])
        glPushMatrix()
        glTranslatef(0, 0, 0.1)
        glScalef(0.12, 2.0, 0.08)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 指板
        glColor4f(*self.colors['rosewood'])
        glPushMatrix()
        glTranslatef(0, 1.0, 0.11)
        glScalef(0.15, 2.0, 0.02)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 品格线（20品）
        glColor4f(*self.colors['nickel'])
        for i in range(1, 21):  # 从第1品到第20品
            y_pos = 1.0 - (i * 0.1)  # 每品距离0.1单位
            glPushMatrix()
            glTranslatef(0, y_pos, 0.115)
            glScalef(0.15, 0.005, 0.01)
            self.draw_cube(1.0)
            glPopMatrix()
        
        # 品记（第3,5,7,9,12,15,17,19品有侧标记）
        dot_positions = [3, 5, 7, 9, 12, 15, 17, 19]
        for pos in dot_positions:
            y_pos = 1.0 - (pos * 0.1)
            glColor4f(1.0, 1.0, 0.0, 1.0)  # 黄色品记
            glPushMatrix()
            glTranslatef(0.09, y_pos, 0.115)
            self.draw_sphere(0.01, 10, 10)
            glPopMatrix()
        
        # 琴头
        glColor4f(*self.colors['maple'])
        glPushMatrix()
        glTranslatef(0, 2.05, 0.1)
        glScalef(0.25, 0.3, 0.08)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 调音钮（6个）
        glColor4f(*self.colors['nickel'])
        for i in range(6):
            x_pos = -0.1 + i * 0.04
            y_pos = 2.15 + (abs(i-2.5) * 0.02)  # 稍微错开位置
            
            # 调音钮柱
            glPushMatrix()
            glTranslatef(x_pos, y_pos, 0.1)
            glRotatef(90, 1, 0, 0)
            self.draw_cylinder(0.01, 0.1, 10)
            glPopMatrix()
            
            # 调音钮头
            glPushMatrix()
            glTranslatef(x_pos, y_pos, 0.15)
            self.draw_sphere(0.02, 10, 10)
            glPopMatrix()
        
        # 弦枕
        glColor4f(*self.colors['plastic_white'])
        glPushMatrix()
        glTranslatef(0, 2.0, 0.11)
        glScalef(0.13, 0.02, 0.02)
        self.draw_cube(1.0)
        glPopMatrix()
    
    def draw_guitar_strings(self):
        """绘制吉他弦"""
        for i in range(6):
            # 计算弦的位置
            x_pos = -0.12 + i * 0.048
            base_y = -0.6  # 琴桥位置
            end_y = 2.0    # 弦枕位置
            
            # 振动效果
            vibration = self.string_vibration[i] * math.sin(
                self.animation_time * 20 * self.string_tension[i] + i * 2
            )
            
            # 弦的颜色
            glColor4f(*self.colors['string_colors'][i])
            
            # 绘制弦（使用线框模式显示振动）
            glBegin(GL_LINE_STRIP)
            segments = 50
            for j in range(segments + 1):
                t = j / segments
                y_pos = base_y + (end_y - base_y) * t
                
                # 振动位移（正弦波形状）
                displacement = vibration * math.sin(t * math.pi)
                x_displacement = x_pos + displacement * 0.05
                
                glVertex3f(x_displacement, y_pos, 0.15)
            glEnd()
            
            # 更新振动衰减
            if self.string_plucked[i]:
                self.string_vibration[i] *= self.vibration_decay
                if self.string_vibration[i] < 0.01:
                    self.string_plucked[i] = False
                    self.string_vibration[i] = 0.0
    
    def pluck_string(self, string_index: int, strength: float = 1.0):
        """弹拨吉他弦"""
        if 0 <= string_index < 6:
            self.string_plucked[string_index] = True
            self.string_vibration[string_index] = strength
            self.string_tension[string_index] = 1.0 + (string_index * 0.1)  # 低音弦张力更大
    
    def draw_guitar_stand(self):
        """绘制吉他支架"""
        glColor4f(0.5, 0.5, 0.5, 1.0)  # 灰色支架
        
        # 支架底座
        glPushMatrix()
        glTranslatef(0, -1.0, 0)
        glScalef(1.5, 0.1, 0.8)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 支架支柱
        glPushMatrix()
        glTranslatef(0, -0.5, 0)
        glScalef(0.1, 0.8, 0.1)
        self.draw_cube(1.0)
        glPopMatrix()
        
        # 支架顶部（支撑吉他的部分）
        glPushMatrix()
        glTranslatef(0, -0.1, 0.2)
        glRotatef(-15, 1, 0, 0)
        glScalef(0.4, 0.05, 0.4)
        self.draw_cube(1.0)
        glPopMatrix()
    
    def update_animation(self, delta_time: float):
        """更新动画"""
        self.animation_time += delta_time
    
    def render(self):
        """渲染整个场景"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # 设置相机
        gluLookAt(
            0, 2, 5,      # 相机位置
            0, 0, 0,      # 观察点
            0, 1, 0       # 上方向
        )
        
        # 应用吉他变换
        glPushMatrix()
        glTranslatef(*self.guitar_position)
        glRotatef(self.guitar_rotation[0], 1, 0, 0)
        glRotatef(self.guitar_rotation[1], 0, 1, 0)
        glRotatef(self.guitar_rotation[2], 0, 0, 1)
        
        # 绘制吉他
        self.draw_guitar_stand()
        self.draw_guitar_body()
        self.draw_guitar_neck()
        self.draw_guitar_strings()
        
        glPopMatrix()
        
        # 添加一些环境元素
        self.draw_environment()
    
    def draw_environment(self):
        """绘制环境元素"""
        # 简单的网格地板
        glColor4f(0.3, 0.3, 0.35, 1.0)
        glBegin(GL_LINES)
        for i in range(-5, 6):
            glVertex3f(i, -1, -5)
            glVertex3f(i, -1, 5)
            glVertex3f(-5, -1, i)
            glVertex3f(5, -1, i)
        glEnd()
        
        # 背景墙（简化）
        glColor4f(0.2, 0.25, 0.3, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(-5, -1, -5)
        glVertex3f(5, -1, -5)
        glVertex3f(5, 5, -5)
        glVertex3f(-5, 5, -5)
        glEnd()
    
    def rotate_guitar(self, x: float, y: float, z: float):
        """旋转吉他"""
        self.guitar_rotation[0] = (self.guitar_rotation[0] + x) % 360
        self.guitar_rotation[1] = (self.guitar_rotation[1] + y) % 360
        self.guitar_rotation[2] = (self.guitar_rotation[2] + z) % 360
    
    def reset_view(self):
        """重置视图"""
        self.guitar_rotation = [15, -30, 0]
        self.guitar_position = [0, -0.5, -5]


class Guitar3DDisplay:
    """吉他3D显示管理器"""
    
    def __init__(self):
        self.guitar_model = Guitar3DModel()
        self.running = True
        self.clock = pygame.time.Clock()
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        self.display_mode = "full"  # full, side, mini
        
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.guitar_model.reset_view()
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, 
                                  pygame.K_4, pygame.K_5, pygame.K_6]:
                    string_index = event.key - pygame.K_1
                    self.guitar_model.pluck_string(string_index, 0.5)
                elif event.key == pygame.K_SPACE:
                    # 随机弹拨一根弦
                    import random
                    string_index = random.randint(0, 5)
                    strength = random.uniform(0.3, 0.8)
                    self.guitar_model.pluck_string(string_index, strength)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self.mouse_dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # 滚轮上
                    self.guitar_model.guitar_position[2] += 0.5
                elif event.button == 5:  # 滚轮下
                    self.guitar_model.guitar_position[2] -= 0.5
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    self.guitar_model.rotate_guitar(dy * 0.5, dx * 0.5, 0)
                    self.last_mouse_pos = event.pos
    
    def render_text_overlay(self):
        """渲染文本叠加层"""
        # 使用pygame渲染文本
        font = pygame.font.Font(None, 36)
        
        instructions = [
            "鼠标拖动: 旋转吉他",
            "滚轮: 缩放",
            "1-6: 弹拨对应弦",
            "空格: 随机弹拨",
            "R: 重置视图",
            "ESC: 退出"
        ]
        
        y_offset = 10
        for instruction in instructions:
            text = font.render(instruction, True, (255, 255, 255))
            pygame.display.get_surface().blit(text, (10, y_offset))
            y_offset += 30
    
    def run(self):
        """运行主循环"""
        print("🎸 吉他3D建模系统启动")
        print("控制说明:")
        print("  鼠标拖动: 旋转吉他视角")
        print("  鼠标滚轮: 缩放视图")
        print("  数字键1-6: 弹拨对应弦（1=高音E弦，6=低音E弦）")
        print("  空格键: 随机弹拨一根弦")
        print("  R键: 重置视图")
        print("  ESC键: 退出")
        
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0
            
            self.handle_events()
            self.guitar_model.update_animation(delta_time)
            self.guitar_model.render()
            
            # 渲染文本叠加层
            self.render_text_overlay()
            
            pygame.display.flip()
        
        pygame.quit()


def create_mini_guitar_view(width=400, height=300):
    """创建小型吉他视图（用于嵌入到其他界面中）"""
    model = Guitar3DModel(width, height)
    
    def render_mini_view():
        model.update_animation(0.016)  # 假设60fps
        model.render()
        pygame.display.flip()
    
    return model, render_mini_view


# 示例：在Streamlit中嵌入吉他3D视图
class StreamlitGuitar3D:
    """Streamlit中的吉他3D视图组件"""
    
    def __init__(self):
        import streamlit as st
        self.st = st
        
    def render_guitar_controls(self):
        """渲染吉他控制界面"""
        st = self.st
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🎸 吉他控制")
            if st.button("重置视图", key="reset_view"):
                pass
            
            string_to_pluck = st.selectbox(
                "选择弦弹拨",
                ["高音E弦 (1)", "B弦 (2)", "G弦 (3)", "D弦 (4)", "A弦 (5)", "低音E弦 (6)"],
                key="string_select"
            )
            
            if st.button("弹拨!", key="pluck_string"):
                string_index = ["高音E弦 (1)", "B弦 (2)", "G弦 (3)", 
                               "D弦 (4)", "A弦 (5)", "低音E弦 (6)"].index(string_to_pluck)
                pass
        
        with col2:
            st.subheader("🎨 外观设置")
            wood_type = st.selectbox(
                "木材类型",
                ["桃花心木", "玫瑰木", "枫木", "乌木"],
                key="wood_type"
            )
            
            string_color = st.color_picker("弦颜色", "#E6E6E6", key="string_color")
        
        with col3:
            st.subheader("📐 视角控制")
            rotation_x = st.slider("X轴旋转", -180, 180, 15, key="rot_x")
            rotation_y = st.slider("Y轴旋转", -180, 180, -30, key="rot_y")
            zoom = st.slider("缩放", 3.0, 10.0, 5.0, key="zoom")
    
    def render_guitar_info(self):
        """渲染吉他信息"""
        st = self.st
        
        with st.expander("ℹ️ 吉他规格信息", expanded=True):
            st.markdown("""
            ### 🎸 电吉他规格
            - **琴型**: Stratocaster风格
            - **琴身木材**: 桃花心木
            - **琴颈木材**: 枫木
            - **指板木材**: 玫瑰木
            - **品数**: 22品
            - **琴桥**: 固定琴桥
            - **拾音器**: 单单双配置
            - **控制**: 1音量，2音色，5档切换
            """)
        
        with st.expander("🎵 标准调弦", expanded=True):
            st.markdown("""
            ### 从高音到低音：
            1. **E4** (高音E弦) - 329.63 Hz
            2. **B** - 246.94 Hz
            3. **G** - 196.00 Hz
            4. **D** - 146.83 Hz
            5. **A** - 110.00 Hz
            6. **E2** (低音E弦) - 82.41 Hz
            """)
    
    def create_guitar_embed(self):
        """创建吉他嵌入视图"""
        st = self.st
        
        # 使用HTML/Canvas嵌入3D视图
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3 style="color: white; text-align: center;">🎸 3D吉他模型</h3>
            <div id="guitar-canvas-container" style="width: 100%; height: 500px; 
                    background: rgba(0,0,0,0.2); border-radius: 8px; 
                    display: flex; align-items: center; justify-content: center;">
                <p style="color: white;">3D吉他视图将在主应用中显示</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    # 单独运行3D吉他查看器
    display = Guitar3DDisplay()
    display.run()
