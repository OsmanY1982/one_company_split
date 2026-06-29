# -*- coding: utf-8 -*-
"""
程序化天体纹理生成器 — 为无真实纹理的卫星/矮行星生成类Perlin噪声表面
"""
import numpy as np


def _upsample_2d(grid, target_h, target_w):
    """纯 numpy 双线性插值上采样，替代 scipy.ndimage.zoom"""
    src_h, src_w = grid.shape
    y_ratio = np.linspace(0, src_h - 1, target_h)
    x_ratio = np.linspace(0, src_w - 1, target_w)
    y0 = np.floor(y_ratio).astype(int)
    y1 = np.minimum(y0 + 1, src_h - 1)
    x0 = np.floor(x_ratio).astype(int)
    x1 = np.minimum(x0 + 1, src_w - 1)
    wy = (y_ratio - y0)[:, None]
    wx = (x_ratio - x0)[None, :]
    q00 = grid[y0[:, None], x0[None, :]]
    q10 = grid[y1[:, None], x0[None, :]]
    q01 = grid[y0[:, None], x1[None, :]]
    q11 = grid[y1[:, None], x1[None, :]]
    return (1 - wy) * (1 - wx) * q00 + wy * (1 - wx) * q10 + (1 - wy) * wx * q01 + wy * wx * q11


def _fbm_noise(width, height, seed=0, octaves=4, lacunarity=2.0, gain=0.5):
    """分形布朗运动噪声 (2D)，纯 numpy 实现"""
    np.random.seed(seed)
    noise = np.zeros((height, width), dtype=np.float64)
    max_val = 0.0
    
    for octave in range(octaves):
        freq = lacunarity ** octave
        amp = gain ** octave
        max_val += amp
        
        nx = max(2, int(width / (8 * freq)))
        ny = max(2, int(height / (8 * freq)))
        grid = np.random.rand(ny, nx).astype(np.float64) * 2 - 1
        
        if nx != width or ny != height:
            upscaled = _upsample_2d(grid, height, width)
        else:
            upscaled = grid
        
        noise += amp * upscaled
    
    noise /= max_val
    return np.clip(noise, -1, 1)


def _apply_colormap(noise, colors, contrast=1.2):
    """将噪声映射到颜色梯度"""
    h, w = noise.shape
    # 归一化到 [0, 1]
    n = np.clip((noise - noise.min()) / (noise.max() - noise.min() + 1e-8), 0, 1)
    n = np.power(n, 1.0 / contrast)  # 对比度调整
    
    result = np.zeros((h, w, 3), dtype=np.uint8)
    n_segments = len(colors) - 1
    
    for i in range(n_segments):
        t0 = i / n_segments
        t1 = (i + 1) / n_segments
        mask = (n >= t0) & (n < t1)
        if i == n_segments - 1:
            mask = n >= t0
        
        frac = np.clip((n[mask] - t0) / (t1 - t0 + 1e-8), 0, 1)
        c0 = np.array(colors[i], dtype=np.float64)
        c1 = np.array(colors[i + 1], dtype=np.float64)
        
        for ch in range(3):
            result[:, :, ch][mask] = (c0[ch] + (c1[ch] - c0[ch]) * frac).astype(np.uint8)
    
    return result


def make_crater_noise(noise, crater_count=30, min_r=2, max_r=8):
    """在噪声图上叠加陨石坑"""
    h, w = noise.shape
    result = noise.copy()
    np.random.seed(42)
    
    for _ in range(crater_count):
        cx = np.random.randint(0, w)
        cy = np.random.randint(0, h)
        r = np.random.randint(min_r, max_r)
        
        yv, xv = np.ogrid[:h, :w]
        dist = np.sqrt((xv - cx)**2 + (yv - cy)**2)
        mask = dist <= r
        
        # 陨石坑：中心暗，边缘亮
        depth_mask = mask.astype(np.float64) * (1.0 - np.clip(dist / (r + 1e-8), 0, 1) * 0.8)
        result -= depth_mask * 0.3
    
    return np.clip(result, -1, 1)


# ── 预设卫星纹理配置 ──

MOON_TEXTURE_PRESETS = {
    "io": {
        "colors": [(200, 160, 30), (220, 180, 50), (170, 120, 20), (240, 200, 80),
                    (160, 100, 10), (200, 150, 40)],
        "octaves": 5, "contrast": 1.5,
    },
    "europa": {
        "colors": [(200, 205, 210), (220, 225, 230), (180, 185, 195), (210, 215, 220),
                    (230, 235, 240), (195, 200, 205)],
        "octaves": 4, "contrast": 1.8,
    },
    "ganymede": {
        "colors": [(120, 110, 100), (140, 130, 115), (100, 90, 80), (155, 140, 125),
                    (90, 80, 70), (130, 120, 105)],
        "octaves": 5, "contrast": 1.4,
    },
    "callisto": {
        "colors": [(80, 75, 70), (100, 95, 90), (60, 55, 50), (90, 85, 80),
                    (70, 65, 60), (110, 105, 100)],
        "octaves": 4, "contrast": 1.3,
    },
    "titan": {
        "colors": [(180, 140, 60), (210, 170, 80), (150, 110, 40), (200, 160, 70),
                    (170, 130, 50), (220, 180, 90)],
        "octaves": 3, "contrast": 1.2,
    },
    "enceladus": {
        "colors": [(230, 235, 240), (240, 245, 250), (220, 225, 230), (235, 240, 245),
                    (245, 248, 252), (225, 230, 235)],
        "octaves": 5, "contrast": 2.0,
    },
    # ── 大型卫星程序化纹理（无真实纹理可用）──
    "triton": {
        "colors": [(180, 160, 170), (200, 180, 190), (160, 140, 155), (190, 170, 180),
                    (210, 190, 200), (170, 150, 165)],
        "octaves": 5, "contrast": 1.6,
    },
    "titania": {
        "colors": [(140, 135, 140), (160, 155, 160), (120, 115, 120), (150, 145, 150),
                    (170, 165, 170), (130, 125, 130)],
        "octaves": 4, "contrast": 1.5,
    },
    "rhea": {
        "colors": [(200, 195, 190), (220, 215, 210), (180, 175, 170), (210, 205, 200),
                    (230, 225, 220), (190, 185, 180)],
        "octaves": 4, "contrast": 1.4,
    },
    "oberon": {
        "colors": [(100, 90, 85), (120, 110, 100), (80, 70, 65), (110, 100, 90),
                    (130, 120, 110), (90, 80, 75)],
        "octaves": 4, "contrast": 1.3,
    },
    "iapetus": {
        "colors": [(90, 85, 80), (180, 170, 155), (70, 65, 60), (120, 110, 95),
                    (200, 190, 170), (85, 80, 70)],
        "octaves": 4, "contrast": 1.8,
    },
    "charon": {
        "colors": [(140, 110, 100), (160, 130, 115), (120, 90, 80), (150, 120, 105),
                    (170, 140, 125), (130, 100, 90)],
        "octaves": 5, "contrast": 1.5,
    },
    "umbriel": {
        "colors": [(80, 75, 80), (95, 90, 95), (65, 60, 65), (90, 85, 90),
                    (105, 100, 105), (70, 65, 70)],
        "octaves": 3, "contrast": 1.3,
    },
    "ariel": {
        "colors": [(170, 165, 170), (190, 185, 190), (150, 145, 150), (180, 175, 180),
                    (200, 195, 200), (160, 155, 160)],
        "octaves": 5, "contrast": 1.6,
    },
    "dione": {
        "colors": [(190, 185, 180), (210, 205, 200), (170, 165, 160), (200, 195, 190),
                    (220, 215, 210), (180, 175, 170)],
        "octaves": 4, "contrast": 1.5,
    },
    "tethys": {
        "colors": [(210, 205, 200), (230, 225, 220), (190, 185, 180), (220, 215, 210),
                    (240, 235, 230), (200, 195, 190)],
        "octaves": 4, "contrast": 1.6,
    },
}


def _auto_preset(body_key):
    """无专用预设时，基于哈希生成确定性配色和参数，每颗卫星外观唯一。"""
    import hashlib
    h = int(hashlib.md5(body_key.encode()).hexdigest()[:8], 16)
    np.random.seed(h)
    # 生成 5-6 个颜色
    n_colors = 5 + (h % 2)
    base_h = np.random.randint(0, 360)
    base_s = np.random.randint(20, 90)
    base_v = np.random.randint(40, 200)
    colors = []
    for i in range(n_colors):
        dh = np.random.randint(-25, 25)
        ds = np.random.randint(-20, 20)
        dv = np.random.randint(-25, 25)
        hsv = (base_h + dh) % 360, min(255, max(30, base_s + ds)), min(255, max(30, base_v + dv))
        # HSV→RGB 简化版
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hsv[0] / 360, hsv[1] / 255, hsv[2] / 255)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    octaves = 3 + (h % 3)
    contrast = 1.0 + (h % 100) / 100.0
    return {"colors": colors, "octaves": octaves, "contrast": contrast}


def generate_moon_texture(body_key, width=256, height=128):
    """
    为指定卫星生成等角矩形程序化纹理。
    有专属预设（MOON_TEXTURE_PRESETS）则用专属；否则自动生成。
    返回 (H, W, 4) RGBA numpy 数组，可直接送入 texture_mapper。
    """
    import sys
    preset = MOON_TEXTURE_PRESETS.get(body_key)
    if preset is None:
        # auto-generate deterministic preset based on name hash
        preset = _auto_preset(body_key)
    
    noise = _fbm_noise(width, height, seed=hash(body_key) % 2**31,
                        octaves=preset["octaves"], gain=0.55)
    
    # 陨石坑叠加
    if body_key in ("ganymede", "callisto"):
        noise = make_crater_noise(noise, crater_count=40 if body_key == "callisto" else 25,
                                  min_r=2, max_r=10)
    
    rgb = _apply_colormap(noise, preset["colors"], contrast=preset["contrast"])
    
    # 拼接成 RGBA
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255
    
    return rgba
