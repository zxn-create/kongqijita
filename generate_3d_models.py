import numpy as np
import open3d as o3d
import os
from PIL import Image

def create_guitar_body():
    """生成吉他琴身3D模型"""
    # 创建琴身（简化椭圆体）
    body = o3d.geometry.TriangleMesh.create_sphere(radius=0.5)
    body.scale(1.5, [1.0, 0.7, 0.3])  # 拉伸成吉他形状
    body.paint_uniform_color([0.4, 0.2, 0.1])  # 木色
    
    # 添加音孔 - 使用布尔运算的新方法
    soundhole = o3d.geometry.TriangleMesh.create_torus(torus_radius=0.3, tube_radius=0.05)
    soundhole.translate([0, 0.1, 0])
    
    # 新版本的布尔运算方法
    try:
        # 尝试使用新版本的布尔差集
        body = body.boolean_difference(soundhole)
    except:
        # 如果失败，使用替代方案：在视觉上创建音孔效果
        print("⚠️  布尔运算失败，使用替代方案创建音孔")
        # 在音孔位置创建凹陷效果
        vertices = np.asarray(body.vertices)
        colors = np.asarray(body.vertex_colors)
        
        # 找到音孔区域的顶点
        soundhole_center = np.array([0, 0.1, 0])
        distances = np.linalg.norm(vertices - soundhole_center, axis=1)
        hole_indices = distances < 0.35
        
        # 将这些顶点向内移动
        directions = vertices[hole_indices] - soundhole_center
        directions = directions / (np.linalg.norm(directions, axis=1, keepdims=True) + 1e-8)
        vertices[hole_indices] -= directions * 0.1
        
        body.vertices = o3d.utility.Vector3dVector(vertices)
    
    return body

def create_guitar_neck():
    """生成吉他琴颈3D模型"""
    # 琴颈主体
    neck = o3d.geometry.TriangleMesh.create_cylinder(radius=0.03, height=2.0)
    neck.paint_uniform_color([0.3, 0.2, 0.1])
    
    # 指板
    fretboard = o3d.geometry.TriangleMesh.create_box(width=0.06, height=1.8, depth=0.01)
    fretboard.translate([-0.03, -0.9, 0.02])
    fretboard.paint_uniform_color([0.1, 0.05, 0.02])
    
    # 添加品格线 - 使用新的合并方法
    frets = []
    for i in range(20):
        fret = o3d.geometry.TriangleMesh.create_box(width=0.07, height=0.005, depth=0.005)
        fret.translate([-0.035, -0.9 + i*0.1, 0.025])
        fret.paint_uniform_color([0.8, 0.8, 0.8])
        frets.append(fret)
    
    # 合并所有网格
    combined_neck = neck
    combined_neck += fretboard
    for fret in frets:
        combined_neck += fret
    
    return combined_neck

def create_textures():
    """生成基础纹理贴图"""
    # 木纹纹理
    wood_texture = create_wood_texture(512, 512)
    wood_texture.save("assets/3d_models/textures/wood_texture.png")
    
    # 金属纹理
    metal_texture = create_metal_texture(512, 512)
    metal_texture.save("assets/3d_models/textures/metal_texture.png")

def create_wood_texture(width, height):
    """生成木纹纹理"""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (width, height), color=(101, 67, 33))
    draw = ImageDraw.Draw(img)
    
    # 添加木纹线条
    for i in range(100):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        length = np.random.randint(50, 200)
        width_line = np.random.randint(1, 3)
        color_variation = np.random.randint(-10, 10)
        color = (101+color_variation, 67+color_variation, 33+color_variation)
        draw.line([(x, y), (x+length, y)], fill=color, width=width_line)
    
    return img

def create_metal_texture(width, height):
    """生成金属纹理"""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (width, height), color=(150, 150, 160))
    draw = ImageDraw.Draw(img)
    
    # 添加金属光泽效果
    for i in range(50):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        size = np.random.randint(10, 30)
        brightness = np.random.randint(180, 220)
        draw.ellipse([x, y, x+size, y+size], fill=(brightness, brightness, brightness))
    
    return img

def create_particle_textures():
    """生成粒子效果纹理"""
    # 火花纹理
    sparkle = create_circle_texture(64, 64, (255, 255, 200))
    sparkle.save("assets/particle_textures/sparkle.png")
    
    # 光晕纹理
    glow = create_glow_texture(128, 128)
    glow.save("assets/particle_textures/glow.png")
    
    # 轨迹纹理
    trail = create_trail_texture(256, 64)
    trail.save("assets/particle_textures/trail.png")

def create_circle_texture(width, height, color):
    """生成圆形纹理"""
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width//2, height//2)
    radius = min(width, height) // 2 - 2
    draw.ellipse([center[0]-radius, center[1]-radius, 
                 center[0]+radius, center[1]+radius], 
                fill=color)
    return img

def create_glow_texture(width, height):
    """生成光晕纹理"""
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = (width//2, height//2)
    
    # 创建多层光晕
    for i in range(5, 0, -1):
        radius = (width // 2) * i // 5
        alpha = 50 - i * 8
        color = (255, 255, 200, alpha)
        draw.ellipse([center[0]-radius, center[1]-radius, 
                     center[0]+radius, center[1]+radius], 
                    fill=color)
    
    return img

def create_trail_texture(width, height):
    """生成轨迹纹理"""
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 创建渐变轨迹
    for i in range(width):
        alpha = int(255 * (1 - i / width))
        color = (100, 200, 255, alpha)
        draw.rectangle([i, 0, i+1, height], fill=color)
    
    return img

def generate_complete_3d_library():
    """生成完整的3D资源库"""
    # 创建目录结构
    os.makedirs("assets/3d_models/textures", exist_ok=True)
    os.makedirs("assets/particle_textures", exist_ok=True)
    
    print("🎸 生成3D吉他模型...")
    
    try:
        # 生成3D模型
        body = create_guitar_body()
        neck = create_guitar_neck()
        
        # 保存为OBJ文件
        o3d.io.write_triangle_mesh("assets/3d_models/guitar_body.obj", body)
        o3d.io.write_triangle_mesh("assets/3d_models/guitar_neck.obj", neck)
        
        print("✅ 3D模型生成完成")
        
        # 生成纹理
        print("🎨 生成纹理贴图...")
        create_textures()
        create_particle_textures()
        
        print("✅ 纹理生成完成")
        
    except Exception as e:
        print(f"❌ 生成过程中出现错误: {e}")
        print("尝试简化版本...")
        generate_simplified_models()

def generate_simplified_models():
    """生成简化版本的3D模型"""
    print("🔄 使用简化版本生成模型...")
    
    # 简化版吉他身体 - 不使用布尔运算
    body = o3d.geometry.TriangleMesh.create_sphere(radius=0.5)
    body.scale(1.5, [1.0, 0.7, 0.3])
    body.paint_uniform_color([0.4, 0.2, 0.1])
    
    # 简化版琴颈
    neck = o3d.geometry.TriangleMesh.create_cylinder(radius=0.03, height=2.0)
    neck.paint_uniform_color([0.3, 0.2, 0.1])
    
    # 保存模型
    o3d.io.write_triangle_mesh("assets/3d_models/guitar_body_simple.obj", body)
    o3d.io.write_triangle_mesh("assets/3d_models/guitar_neck_simple.obj", neck)
    
    print("✅ 简化版模型生成完成")

if __name__ == "__main__":
    print(f"🔧 使用的Open3D版本: {o3d.__version__}")
    generate_complete_3d_library()
    
    print("📁 生成的文件结构：")
    print("""
assets/
├── 3d_models/
│   ├── guitar_body.obj      # 吉他琴身
│   ├── guitar_neck.obj      # 吉他琴颈
│   └── textures/
│       ├── wood_texture.png  # 木纹贴图
│       └── metal_texture.png # 金属贴图
└── particle_textures/
    ├── sparkle.png          # 火花粒子
    ├── glow.png            # 光晕粒子
    └── trail.png           # 轨迹粒子
    """)
