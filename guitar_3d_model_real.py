# guitar_3d_model_real.py
import numpy as np
from typing import List, Tuple, Dict
import plotly.graph_objects as go
import math

class RealGuitar3DModel:
    """真实吉他形状的3D模型"""
    
    def __init__(self):
        # 吉他尺寸参数（基于真实吉他比例）
        self.guitar_params = {
            # 琴身参数
            'body_length': 20,  # 琴身长度
            'body_width': 12,   # 琴身最宽处
            'body_depth': 2,    # 琴身厚度
            
            # 琴颈参数
            'neck_length': 25,  # 琴颈长度
            'neck_width': 2.5,  # 琴颈宽度
            'neck_thickness': 1, # 琴颈厚度
            
            # 弦参数
            'num_strings': 6,
            'string_length': 45,  # 弦长
            'nut_to_bridge': 43,  # 弦枕到琴桥距离
            
            # 真实吉他曲线参数（基于Stratocaster）
            'upper_bout_radius': 12,  # 上部曲线半径
            'lower_bout_radius': 14,  # 下部曲线半径
            'waist_width': 8,         # 腰部宽度
            'cutaway_depth': 4        # 切角深度
        }
        
        # 颜色定义
        self.colors = {
            'body_sunburst': '#8B4513',  # 日落渐变色（琴身）
            'neck_maple': '#D2B48C',      # 枫木色（琴颈）
            'fretboard_rosewood': '#3A2010',  # 玫瑰木色（指板）
            'fret_nickel': '#C0C0C0',     # 镍色（品丝）
            'strings_steel': '#E0E0E0',   # 钢弦色
            'pickup_black': '#1A1A1A',    # 黑色（拾音器）
            'pickguard_white': '#F5F5F5', # 白色（护板）
            'knobs_chrome': '#DCDCDC',    # 铬色（旋钮）
            'bridge_chrome': '#C0C0C0',   # 铬色（琴桥）
            'dot_white': '#FFFFFF'        # 白色（品记点）
        }
        
        # 振动参数
        self.string_vibration = [0.0] * 6
        self.string_decay = 0.97
        self.time = 0.0
        
    def create_guitar_body_mesh(self):
        """创建真实吉他琴身网格"""
        params = self.guitar_params
        
        # 琴身主要控制点（基于真实吉他形状）
        t = np.linspace(0, 2 * np.pi, 100)
        
        # 上部曲线
        upper_x = params['upper_bout_radius'] * np.cos(t) * 0.8
        upper_y = params['upper_bout_radius'] * np.sin(t) * 1.2 + params['body_length'] * 0.4
        
        # 下部曲线
        lower_x = params['lower_bout_radius'] * np.cos(t) * 0.8
        lower_y = params['lower_bout_radius'] * np.sin(t) * 1.2 - params['body_length'] * 0.4
        
        # 腰部（连接部分）
        waist_x = np.array([-params['waist_width']/2, params['waist_width']/2])
        waist_y = np.array([0, 0])
        
        # 合并所有点形成吉他轮廓
        body_x = []
        body_y = []
        
        # 上部曲线（逆时针）
        for i in range(25, 75):
            body_x.append(upper_x[i])
            body_y.append(upper_y[i])
        
        # 右切角
        cutaway_x = np.linspace(upper_x[74], params['waist_width']/2, 10)
        cutaway_y = np.linspace(upper_y[74], 0, 10)
        body_x.extend(cutaway_x[1:])
        body_y.extend(cutaway_y[1:])
        
        # 腰部右侧
        body_x.append(params['waist_width']/2)
        body_y.append(0)
        
        # 下部曲线
        for i in range(25, 75):
            body_x.append(lower_x[i])
            body_y.append(lower_y[i])
        
        # 左切角
        cutaway_x = np.linspace(-params['waist_width']/2, lower_x[25], 10)
        cutaway_y = np.linspace(0, lower_y[25], 10)
        body_x.extend(cutaway_x[1:])
        body_y.extend(cutaway_y[1:])
        
        # 腰部左侧
        body_x.append(-params['waist_width']/2)
        body_y.append(0)
        
        # 左切角回上部
        cutaway_x = np.linspace(-params['waist_width']/2, upper_x[25], 10)
        cutaway_y = np.linspace(0, upper_y[25], 10)
        body_x.extend(cutaway_x[1:])
        body_y.extend(cutaway_y[1:])
        
        # 转换为numpy数组
        body_x = np.array(body_x)
        body_y = np.array(body_y)
        
        # 创建3D网格
        z_offset = params['body_depth'] / 2
        front_z = np.full_like(body_x, z_offset)
        back_z = np.full_like(body_x, -z_offset)
        
        # 创建顶点
        vertices_x = np.concatenate([body_x, body_x])
        vertices_y = np.concatenate([body_y, body_y])
        vertices_z = np.concatenate([front_z, back_z])
        
        # 创建面（三角形）
        num_points = len(body_x)
        faces = []
        
        # 前面
        for i in range(num_points - 1):
            faces.append([i, i+1, num_points + i])
            faces.append([i+1, num_points + i+1, num_points + i])
        
        # 连接首尾
        faces.append([num_points-1, 0, 2*num_points-1])
        faces.append([0, num_points, 2*num_points-1])
        
        # 侧面
        for i in range(num_points - 1):
            faces.append([i, i+1, (i+1) % num_points])
            faces.append([num_points + i, num_points + i+1, num_points + ((i+1) % num_points)])
        
        return vertices_x, vertices_y, vertices_z, faces
    
    def create_guitar_neck_mesh(self):
        """创建吉他琴颈网格"""
        params = self.guitar_params
        
        # 琴颈主体
        neck_length = params['neck_length']
        neck_width = params['neck_width']
        neck_thickness = params['neck_thickness']
        
        # 顶点
        vertices = [
            # 前表面
            [-neck_width/2, 0, neck_thickness/2],
            [neck_width/2, 0, neck_thickness/2],
            [neck_width/2, neck_length, neck_thickness/2],
            [-neck_width/2, neck_length, neck_thickness/2],
            
            # 后表面
            [-neck_width/2, 0, -neck_thickness/2],
            [neck_width/2, 0, -neck_thickness/2],
            [neck_width/2, neck_length, -neck_thickness/2],
            [-neck_width/2, neck_length, -neck_thickness/2]
        ]
        
        # 面（立方体）
        faces = [
            [0, 1, 2, 3],  # 前
            [4, 7, 6, 5],  # 后
            [0, 4, 5, 1],  # 下
            [2, 6, 7, 3],  # 上
            [0, 3, 7, 4],  # 左
            [1, 5, 6, 2]   # 右
        ]
        
        # 转换为数组
        vertices = np.array(vertices)
        
        return vertices[:, 0], vertices[:, 1], vertices[:, 2], faces
    
    def create_fretboard_mesh(self):
        """创建指板网格"""
        params = self.guitar_params
        
        # 指板尺寸（比琴颈稍宽）
        fretboard_length = params['neck_length'] * 0.9
        fretboard_width = params['neck_width'] + 0.5
        fretboard_thickness = 0.2
        
        # 指板弧度（半径）
        fretboard_radius = 10
        
        # 创建带弧度的指板
        num_points = 20
        t = np.linspace(-fretboard_width/2, fretboard_width/2, num_points)
        
        # 抛物线形状模拟弧度
        z = (t**2) / (2 * fretboard_radius)
        
        vertices_x = []
        vertices_y = []
        vertices_z = []
        
        # 创建顶点
        for y in [0, fretboard_length]:
            for i in range(num_points):
                vertices_x.append(t[i])
                vertices_y.append(y)
                vertices_z.append(z[i] + fretboard_thickness)
        
        # 转换为数组
        vertices_x = np.array(vertices_x)
        vertices_y = np.array(vertices_y)
        vertices_z = np.array(vertices_z)
        
        # 创建面
        faces = []
        for i in range(num_points - 1):
            # 前面
            faces.append([i, i+1, num_points + i])
            faces.append([i+1, num_points + i+1, num_points + i])
        
        return vertices_x, vertices_y, vertices_z, faces
    
    def create_frets(self):
        """创建品丝"""
        params = self.guitar_params
        
        # 品数（标准吉他22品）
        num_frets = 22
        
        # 弦长比例（基于真实吉他品距）
        scale_length = params['nut_to_bridge']
        fret_positions = []
        
        # 计算品位置（基于12平均律）
        for n in range(1, num_frets + 1):
            position = scale_length - (scale_length / (2 ** (n / 12)))
            fret_positions.append(position)
        
        # 创建品丝网格
        fret_width = params['neck_width'] + 0.6
        fret_thickness = 0.05
        fret_height = 0.1
        
        frets_x = []
        frets_y = []
        frets_z = []
        frets_i = []
        frets_j = []
        frets_k = []
        
        idx = 0
        for fret_num, y_pos in enumerate(fret_positions):
            # 品丝顶点
            vertices = [
                [-fret_width/2, y_pos, fret_height],
                [fret_width/2, y_pos, fret_height],
                [fret_width/2, y_pos + fret_thickness, fret_height],
                [-fret_width/2, y_pos + fret_thickness, fret_height]
            ]
            
            for v in vertices:
                frets_x.append(v[0])
                frets_y.append(v[1])
                frets_z.append(v[2])
            
            # 品丝面（两个三角形组成矩形）
            base_idx = idx * 4
            frets_i.extend([base_idx, base_idx + 2])
            frets_j.extend([base_idx + 1, base_idx + 1])
            frets_k.extend([base_idx + 2, base_idx + 3])
            
            idx += 1
        
        return frets_x, frets_y, frets_z, frets_i, frets_j, frets_k
    
    def create_strings(self):
        """创建吉他弦"""
        params = self.guitar_params
        
        strings_x = []
        strings_y = []
        strings_z = []
        strings_i = []
        strings_j = []
        strings_k = []
        
        # 弦位置（从低音到高音）
        string_spacing = (params['neck_width'] - 0.5) / 5
        start_x = -params['neck_width']/2 + 0.25
        
        # 弦的弧度（模拟真实吉他指板弧度）
        fingerboard_radius = 10
        string_height = 0.15
        
        idx = 0
        for string_num in range(6):
            # 弦的x位置
            x_pos = start_x + string_num * string_spacing
            
            # 计算弦的弧度高度
            z_offset = (x_pos**2) / (2 * fingerboard_radius) if abs(x_pos) > 0.1 else 0
            
            # 弦的振动
            vibration = self.string_vibration[string_num] * np.sin(
                self.time * 20 + string_num * 2
            )
            
            # 创建弦的点
            num_points = 50
            y_points = np.linspace(0, params['nut_to_bridge'], num_points)
            
            for i, y in enumerate(y_points):
                # 振动效果（正弦波形状）
                vib_factor = vibration * np.sin(y * np.pi / params['nut_to_bridge'])
                
                strings_x.append(x_pos + vib_factor * 0.1)
                strings_y.append(y)
                strings_z.append(string_height + z_offset)
                
                if i < num_points - 1:
                    base_idx = idx * num_points
                    strings_i.append(base_idx + i)
                    strings_j.append(base_idx + i + 1)
                    strings_k.append(base_idx + i)
            
            idx += 1
        
        return strings_x, strings_y, strings_z, strings_i, strings_j, strings_k
    
    def create_pickups(self):
        """创建拾音器"""
        params = self.guitar_params
        
        # 拾音器位置（琴颈、中间、琴桥）
        pickup_positions = [
            {'name': '琴颈拾音器', 'y': params['body_length'] * 0.3, 'width': 3.2, 'height': 0.8, 'depth': 0.3},
            {'name': '中间拾音器', 'y': params['body_length'] * 0.15, 'width': 3.0, 'height': 0.7, 'depth': 0.3},
            {'name': '琴桥拾音器', 'y': -params['body_length'] * 0.15, 'width': 2.8, 'height': 0.6, 'depth': 0.3}
        ]
        
        pickups_x = []
        pickups_y = []
        pickups_z = []
        pickups_i = []
        pickups_j = []
        pickups_k = []
        
        idx = 0
        for pickup in pickup_positions:
            width = pickup['width']
            height = pickup['height']
            depth = pickup['depth']
            y_pos = pickup['y']
            
            # 创建立方体顶点
            vertices = [
                [-width/2, y_pos - height/2, depth/2],
                [width/2, y_pos - height/2, depth/2],
                [width/2, y_pos + height/2, depth/2],
                [-width/2, y_pos + height/2, depth/2],
                [-width/2, y_pos - height/2, -depth/2],
                [width/2, y_pos - height/2, -depth/2],
                [width/2, y_pos + height/2, -depth/2],
                [-width/2, y_pos + height/2, -depth/2]
            ]
            
            for v in vertices:
                pickups_x.append(v[0])
                pickups_y.append(v[1])
                pickups_z.append(v[2])
            
            # 立方体面
            base_idx = idx * 8
            # 前
            pickups_i.extend([base_idx, base_idx, base_idx + 1, base_idx + 2])
            pickups_j.extend([base_idx + 1, base_idx + 3, base_idx + 2, base_idx + 3])
            pickups_k.extend([base_idx + 2, base_idx + 2, base_idx + 3, base_idx])
            # 后
            pickups_i.extend([base_idx + 4, base_idx + 4, base_idx + 5, base_idx + 6])
            pickups_j.extend([base_idx + 5, base_idx + 7, base_idx + 6, base_idx + 7])
            pickups_k.extend([base_idx + 6, base_idx + 6, base_idx + 7, base_idx + 4])
            # 侧面
            pickups_i.extend([base_idx, base_idx + 1, base_idx + 2, base_idx + 3])
            pickups_j.extend([base_idx + 4, base_idx + 5, base_idx + 6, base_idx + 7])
            pickups_k.extend([base_idx + 5, base_idx + 6, base_idx + 7, base_idx + 4])
            
            idx += 1
        
        return pickups_x, pickups_y, pickups_z, pickups_i, pickups_j, pickups_k
    
    def create_controls(self):
        """创建控制旋钮和开关"""
        params = self.guitar_params
        
        # 控制元件位置
        controls = [
            {'type': 'volume', 'x': -1.5, 'y': params['body_length'] * 0.25, 'radius': 0.3, 'height': 0.2},
            {'type': 'tone1', 'x': 0, 'y': params['body_length'] * 0.25, 'radius': 0.3, 'height': 0.2},
            {'type': 'tone2', 'x': 1.5, 'y': params['body_length'] * 0.25, 'radius': 0.3, 'height': 0.2},
            {'type': 'switch', 'x': 0, 'y': params['body_length'] * 0.35, 'width': 1.0, 'height': 0.1, 'depth': 0.3}
        ]
        
        controls_x = []
        controls_y = []
        controls_z = []
        
        for control in controls:
            if control['type'] == 'switch':
                # 5档开关
                num_points = 20
                t = np.linspace(0, 2 * np.pi, num_points)
                
                for angle in t:
                    x = control['x'] + control['width']/2 * np.cos(angle)
                    y = control['y']
                    z = control['height']/2 * np.sin(angle)
                    
                    controls_x.append(x)
                    controls_y.append(y)
                    controls_z.append(z)
            else:
                # 旋钮（圆柱体）
                num_points = 20
                t = np.linspace(0, 2 * np.pi, num_points)
                
                for angle in t:
                    x = control['x'] + control['radius'] * np.cos(angle)
                    y = control['y']
                    z = control['height']/2 + control['radius'] * 0.3 * np.sin(angle)
                    
                    controls_x.append(x)
                    controls_y.append(y)
                    controls_z.append(z)
        
        return controls_x, controls_y, controls_z
    
    def create_bridge(self):
        """创建琴桥"""
        params = self.guitar_params
        
        # 琴桥尺寸
        bridge_width = 4.0
        bridge_length = 1.0
        bridge_height = 0.3
        
        # 创建琴桥网格
        vertices = [
            [-bridge_width/2, -params['body_length'] * 0.35, bridge_height/2],
            [bridge_width/2, -params['body_length'] * 0.35, bridge_height/2],
            [bridge_width/2, -params['body_length'] * 0.35 + bridge_length, bridge_height/2],
            [-bridge_width/2, -params['body_length'] * 0.35 + bridge_length, bridge_height/2],
            [-bridge_width/2, -params['body_length'] * 0.35, -bridge_height/2],
            [bridge_width/2, -params['body_length'] * 0.35, -bridge_height/2],
            [bridge_width/2, -params['body_length'] * 0.35 + bridge_length, -bridge_height/2],
            [-bridge_width/2, -params['body_length'] * 0.35 + bridge_length, -bridge_height/2]
        ]
        
        bridge_x = [v[0] for v in vertices]
        bridge_y = [v[1] for v in vertices]
        bridge_z = [v[2] for v in vertices]
        
        # 面索引
        i = [0, 0, 4, 4, 0, 1, 2, 3, 4, 5, 6, 7]
        j = [1, 3, 5, 7, 4, 5, 6, 7, 5, 6, 7, 4]
        k = [2, 2, 6, 6, 1, 2, 3, 0, 6, 7, 4, 5]
        
        return bridge_x, bridge_y, bridge_z, i, j, k
    
    def create_headstock(self):
        """创建琴头（Stratocaster风格）"""
        params = self.guitar_params
        
        # 琴头形状控制点
        headstock_points = [
            [-1.5, params['neck_length'] + 1.0],
            [1.5, params['neck_length'] + 1.0],
            [2.0, params['neck_length'] + 3.0],
            [1.2, params['neck_length'] + 4.0],
            [0, params['neck_length'] + 4.5],
            [-1.2, params['neck_length'] + 4.0],
            [-2.0, params['neck_length'] + 3.0],
            [-1.5, params['neck_length'] + 1.0]
        ]
        
        headstock_x = [p[0] for p in headstock_points]
        headstock_y = [p[1] for p in headstock_points]
        headstock_z = [0.1] * len(headstock_points)
        
        # 调音钮位置
        tuning_pegs = []
        for i in range(6):
            x_pos = -1.0 + i * 0.4
            y_pos = params['neck_length'] + 3.5 - abs(i - 2.5) * 0.2
            tuning_pegs.append((x_pos, y_pos))
        
        return headstock_x, headstock_y, headstock_z, tuning_pegs
    
    def update_string_vibration(self, string_index: int, strength: float = 1.0):
        """更新弦振动"""
        if 0 <= string_index < 6:
            self.string_vibration[string_index] = strength
    
    def update_animation(self, delta_time: float):
        """更新动画"""
        self.time += delta_time
        
        # 衰减振动
        for i in range(6):
            self.string_vibration[i] *= self.string_decay
            if self.string_vibration[i] < 0.01:
                self.string_vibration[i] = 0.0
    
    def create_complete_guitar_plot(self, rotation=None, zoom=5.0):
        """创建完整的吉他3D图"""
        if rotation is None:
            rotation = [15, -30, 0]
        
        # 创建图形
        fig = go.Figure()
        
        # 1. 创建琴身
        body_x, body_y, body_z, body_faces = self.create_guitar_body_mesh()
        
        # 将面转换为Plotly格式
        i, j, k = [], [], []
        for face in body_faces:
            if len(face) == 3:
                i.append(face[0])
                j.append(face[1])
                k.append(face[2])
            elif len(face) == 4:
                # 四边形拆分为两个三角形
                i.extend([face[0], face[0]])
                j.extend([face[1], face[2]])
                k.extend([face[2], face[3]])
        
        fig.add_trace(go.Mesh3d(
            x=body_x, y=body_y, z=body_z,
            i=i, j=j, k=k,
            color=self.colors['body_sunburst'],
            opacity=0.9,
            flatshading=True,
            lighting=dict(
                ambient=0.3,
                diffuse=0.8,
                fresnel=0.1,
                specular=1,
                roughness=0.1
            ),
            lightposition=dict(x=100, y=100, z=100),
            name='琴身'
        ))
        
        # 2. 创建琴颈
        neck_x, neck_y, neck_z, neck_faces = self.create_guitar_neck_mesh()
        
        i, j, k = [], [], []
        for face in neck_faces:
            if len(face) == 4:
                i.extend([face[0], face[0]])
                j.extend([face[1], face[2]])
                k.extend([face[2], face[3]])
        
        fig.add_trace(go.Mesh3d(
            x=neck_x, y=neck_y, z=neck_z,
            i=i, j=j, k=k,
            color=self.colors['neck_maple'],
            opacity=0.8,
            name='琴颈'
        ))
        
        # 3. 创建指板
        fb_x, fb_y, fb_z, fb_faces = self.create_fretboard_mesh()
        
        i, j, k = [], [], []
        for i_face in range(len(fb_faces)):
            face = fb_faces[i_face]
            if len(face) == 3:
                i.append(face[0])
                j.append(face[1])
                k.append(face[2])
        
        fig.add_trace(go.Mesh3d(
            x=fb_x, y=fb_y, z=fb_z,
            i=i, j=j, k=k,
            color=self.colors['fretboard_rosewood'],
            opacity=0.9,
            name='指板'
        ))
        
        # 4. 创建品丝
        frets_x, frets_y, frets_z, frets_i, frets_j, frets_k = self.create_frets()
        
        fig.add_trace(go.Mesh3d(
            x=frets_x, y=frets_y, z=frets_z,
            i=frets_i, j=frets_j, k=frets_k,
            color=self.colors['fret_nickel'],
            opacity=0.9,
            name='品丝'
        ))
        
        # 5. 创建弦
        strings_x, strings_y, strings_z, strings_i, strings_j, strings_k = self.create_strings()
        
        fig.add_trace(go.Mesh3d(
            x=strings_x, y=strings_y, z=strings_z,
            i=strings_i, j=strings_j, k=strings_k,
            color=self.colors['strings_steel'],
            opacity=0.9,
            name='琴弦'
        ))
        
        # 6. 创建拾音器
        pickups_x, pickups_y, pickups_z, pickups_i, pickups_j, pickups_k = self.create_pickups()
        
        fig.add_trace(go.Mesh3d(
            x=pickups_x, y=pickups_y, z=pickups_z,
            i=pickups_i, j=pickups_j, k=pickups_k,
            color=self.colors['pickup_black'],
            opacity=0.8,
            name='拾音器'
        ))
        
        # 7. 创建琴桥
        bridge_x, bridge_y, bridge_z, bridge_i, bridge_j, bridge_k = self.create_bridge()
        
        fig.add_trace(go.Mesh3d(
            x=bridge_x, y=bridge_y, z=bridge_z,
            i=bridge_i, j=bridge_j, k=bridge_k,
            color=self.colors['bridge_chrome'],
            opacity=0.9,
            name='琴桥'
        ))
        
        # 8. 创建控制旋钮
        controls_x, controls_y, controls_z = self.create_controls()
        
        fig.add_trace(go.Scatter3d(
            x=controls_x, y=controls_y, z=controls_z,
            mode='markers',
            marker=dict(
                size=5,
                color=self.colors['knobs_chrome'],
                opacity=0.8
            ),
            name='控制旋钮'
        ))
        
        # 9. 创建琴头
        headstock_x, headstock_y, headstock_z, tuning_pegs = self.create_headstock()
        
        # 琴头多边形
        fig.add_trace(go.Scatter3d(
            x=headstock_x + [headstock_x[0]],
            y=headstock_y + [headstock_y[0]],
            z=headstock_z + [headstock_z[0]],
            mode='lines',
            line=dict(color=self.colors['neck_maple'], width=3),
            name='琴头'
        ))
        
        # 调音钮
        for peg_x, peg_y in tuning_pegs:
            fig.add_trace(go.Scatter3d(
                x=[peg_x], y=[peg_y], z=[0.1],
                mode='markers',
                marker=dict(
                    size=6,
                    color=self.colors['knobs_chrome'],
                    symbol='circle'
                ),
                showlegend=False,
                name='调音钮'
            ))
        
        # 设置布局
        fig.update_layout(
            scene=dict(
                xaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-15, 15]
                ),
                yaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-15, 35]
                ),
                zaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    range=[-5, 5]
                ),
                aspectmode='manual',
                aspectratio=dict(x=1.5, y=2, z=0.5),
                camera=dict(
                    eye=dict(
                        x=rotation[0]/45,
                        y=rotation[1]/45,
                        z=zoom/3
                    )
                ),
                bgcolor='rgba(20, 20, 30, 0.9)'
            ),
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.3)',
                borderwidth=1,
                font=dict(color='white', size=10)
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            autosize=True
        )
        
        return fig


# 简化版本用于Streamlit集成
class StreamlitRealGuitar3D:
    """Streamlit中的真实吉他3D模型"""
    
    def __init__(self):
        self.guitar_model = RealGuitar3DModel()
        self.rotation = [15, -30, 0]
        self.zoom = 5.0
        
    def create_interactive_view(self, chord_detected=None, current_chord=None):
        """创建交互式3D视图"""
        # 更新动画
        self.guitar_model.update_animation(0.016)
        
        # 创建吉他图
        fig = self.guitar_model.create_complete_guitar_plot(self.rotation, self.zoom)
        
        # 如果检测到和弦，让所有弦振动
        if chord_detected:
            for i in range(6):
                self.guitar_model.update_string_vibration(i, 0.3)
        
        return fig
    
    def render_compact_view(self, chord_detected=None, current_chord=None):
        """渲染紧凑的3D视图"""
        import streamlit as st
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 创建3D吉他
            fig = self.create_interactive_view(chord_detected, current_chord)
            
            # 显示3D图
            st.plotly_chart(fig, use_container_width=True, height=500, config={
                'displayModeBar': True,
                'scrollZoom': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['select2d', 'lasso2d']
            })
        
        with col2:
            # 控制面板
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(30,30,46,0.8), rgba(20,20,35,0.9)); 
                        padding: 15px; border-radius: 8px; border: 1px solid rgba(100,100,255,0.1);">
                <h4 style="color: white; margin: 0 0 15px 0; text-align: center;">🎸 真实吉他模型</h4>
            """, unsafe_allow_html=True)
            
            # 当前和弦显示
            if current_chord and current_chord != "none":
                chord_colors = {
                    'C_major': '#FF6B6B',
                    'G_major': '#4ECDC4', 
                    'D_major': '#45B7D1',
                    'A_minor': '#96CEB4',
                    'E_minor': '#FFEAA7',
                    'F_major': '#DDA0DD'
                }
                color = chord_colors.get(current_chord, '#FF6B6B')
                
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: {color}20; 
                            border-radius: 6px; margin: 10px 0; border: 1px solid {color}40;">
                    <p style="margin: 0; color: white; font-weight: bold;">🎵 当前和弦</p>
                    <p style="margin: 0; color: {color}; font-size: 1.3em; font-weight: bold;">{current_chord}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 控制按钮
            if st.button("🎵 弹奏测试", key="play_test", use_container_width=True):
                # 随机弹拨一根弦
                import random
                string_idx = random.randint(0, 5)
                self.guitar_model.update_string_vibration(string_idx, 0.5)
                st.rerun()
            
            if st.button("🔄 重置视图", key="reset_3d", use_container_width=True):
                self.rotation = [15, -30, 0]
                self.zoom = 5.0
                st.rerun()
            
            # 视角控制
            st.markdown("---")
            st.markdown("**📐 视角控制**")
            
            self.rotation[0] = st.slider(
                "上下倾斜", -90, 90, self.rotation[0],
                key="tilt_slider",
                help="控制吉他上下角度"
            )
            
            self.rotation[1] = st.slider(
                "左右旋转", -180, 180, self.rotation[1],
                key="rotate_slider",
                help="控制吉他左右旋转"
            )
            
            self.zoom = st.slider(
                "缩放", 3.0, 8.0, self.zoom, 0.1,
                key="zoom_slider",
                help="控制视图远近"
            )
            
            # 吉他信息
            st.markdown("---")
            st.markdown("**ℹ️ 吉他规格**")
            st.markdown("""
            <div style="font-size: 0.8em; color: #aaa;">
                <p style="margin: 2px 0;">🎸 琴型: Stratocaster</p>
                <p style="margin: 2px 0;">🪵 材质: 日落渐变漆面</p>
                <p style="margin: 2px 0;">🎵 弦数: 6弦钢弦</p>
                <p style="margin: 2px 0;">📍 品数: 22品</p>
                <p style="margin: 2px 0;">⚡ 渲染: 高细节模型</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)


# 测试代码
if __name__ == "__main__":
    import streamlit as st
    
    st.set_page_config(
        page_title="真实吉他3D模型",
        page_icon="🎸",
        layout="wide"
    )
    
    st.title("🎸 真实吉他3D模型展示")
    
    guitar_view = StreamlitRealGuitar3D()
    guitar_view.render_compact_view(
        chord_detected=True,
        current_chord="C_major"
    )
