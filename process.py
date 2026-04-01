import os
import glob
import re
import time  # 導入時間模組
from google import genai
from google.genai import types

# --- 1. 初始化最新 SDK ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.0-flash" 

categories = {
    "上半身": ["掛脖背心", "馬甲背心", "細肩帶背心", "削肩背心", "短版T恤", "襯衫", "一字領上衣"],
    "下半身": ["熱褲", "高腰長褲", "百褶裙", "包臀裙", "牛仔長裙", "工裝褲", "瑜珈褲"],
    "連身裙": ["短版連身裙", "膝上連身裙", "過膝連身裙"],
    "外搭": ["西裝外套", "針織開衫", "牛仔夾克", "透膚襯衫", "皮衣"],
    "襪類": ["透膚黑絲", "白色長襪", "網襪", "膝上襪", "隱形襪"],
    "鞋類": ["細高跟鞋", "老爹鞋", "瑪莉珍鞋", "膝上靴", "帆布鞋", "涼鞋"],
    "風格": ["法式優雅", "性感辣妹", "清新甜美", "商務幹練", "美式街頭", "極簡冷淡", "Y2K"]
}

# 設定安全等級與生成配置
config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ],
    temperature=0.1
)

# --- 2. 處理照片 ---
image_files = glob.glob("processed_images/*.*")
print(f"找到 {len(image_files)} 個檔案，準備開始處理...")

for filepath in image_files:
    filename = os.path.basename(filepath)
    
    # 跳過已命名好的檔案或隱藏檔
    if filename == ".keep" or filename.count('-') >= 5:
        continue

    try:
        print(f"正在辨識: {filename}...")
        
        with open(filepath, "rb") as f:
            img_data = f.read()
        
        image = types.Part.from_bytes(data=img_data, mime_type="image/jpeg")
        prompt = f"分析穿搭並回傳格式：[上身]-[下身]-[連身裙]-[外搭]-[襪]-[鞋]_[風格]。字典：{categories}. 只回傳字串結果。"
        
        # 執行辨識
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image],
            config=config
        )
        
        result = response.text.strip().replace(" ", "")
        clean_name = re.sub(r'[^\w\s-]', '', result)
        ext = os.path.splitext(filename)[1]
        
        new_path = f"processed_images/{clean_name}{ext}"
        os.rename(filepath, new_path)
        print(f"✅ 成功: {filename} -> {clean_name}{ext}")

        # --- 🕒 核心修正：每張照片處理完後休息 10 秒，避免觸發 429 錯誤 ---
        print("等待 10 秒以符合免費版頻率限制...")
        time.sleep(10)

    except Exception as e:
        print(f"❌ 錯誤: {filename} - {e}")
        # 即使報錯也休息一下，避免連續撞牆
        time.sleep(5)
