import os
import glob
import re
from PIL import Image
import numpy as np

print("🔥 FREE MODE RUNNING (NO API) 🔥")


def analyze_image_style(image_path):
    """用顏色判斷風格（簡易版 AI）"""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((100, 100))

    arr = np.array(img)
    avg_color = arr.mean(axis=(0, 1))  # RGB 平均

    r, g, b = avg_color

    # 👉 簡單規則判斷風格
    if r > 180 and g > 180 and b > 180:
        return "極簡冷淡"
    elif r > 180 and g > 150:
        return "清新甜美"
    elif r > 150 and b < 100:
        return "性感辣妹"
    elif g > 150:
        return "自然清新"
    elif b > 150:
        return "冷色系"
    else:
        return "日常穿搭"


def generate_name(style):
    """生成檔名"""
    return f"無-無-無-無-無-無_{style}"


def get_unique_path(path):
    if not os.path.exists(path):
        return path

    name, ext = os.path.splitext(path)
    i = 1

    while True:
        new_path = f"{name}_{i}{ext}"
        if not os.path.exists(new_path):
            return new_path
        i += 1


for filepath in glob.glob("processed_images/*.*"):
    filename = os.path.basename(filepath)

    if filename == ".keep" or filename.count('-') >= 5:
        continue

    try:
        print(f"🔍 分析中: {filename}")

        style = analyze_image_style(filepath)
        new_name = generate_name(style)

        clean_name = re.sub(r'[\\/:*?"<>|]', '', new_name)

        ext = os.path.splitext(filename)[1]
        new_path = f"processed_images/{clean_name}{ext}"

        new_path = get_unique_path(new_path)

        os.rename(filepath, new_path)

        print(f"✅ 改名成功: {os.path.basename(new_path)}")

    except Exception as e:
        print(f"❌ 錯誤: {filename} - {e}")
