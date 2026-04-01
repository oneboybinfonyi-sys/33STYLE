import os
import glob
import re
import time
from google import genai
from google.genai import types
from google.api_core import exceptions

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

config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    ],
    temperature=0.1
)

# --- 2. 處理照片 ---
image_files = glob.glob("processed_images/*.*")
print(f"🚀 找到 {len(image_files)} 個檔案，準備開始處理...")

for filepath in image_files:
    filename = os.path.basename(filepath)
    
    # 跳過已命名好的檔案 (檔名包含底線或多個連字號視為已處理)
    if filename == ".keep" or filename.count('-') >= 5:
        continue

    # --- 🔄 自動重試邏輯 ---
    success = False
    retry_count = 0
    max_retries = 3

    while not success and retry_count < max_retries:
        try:
            print(f"正在辨識 ({retry_count+1}/{max_retries}): {filename}...")
            with open(filepath, "rb") as f:
                img_data = f.read()
            
            image = types.Part.from_bytes(data=img_data, mime_type="image/jpeg")
            prompt = f"分析穿搭並回傳格式：[上身]-[下身]-[連身裙]-[外搭]-[襪]-[鞋]_[風格]。字典：{categories}. 只回傳字串。"
            
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
            
            success = True
            # 每張成功後固定休息 10 秒，保持禮貌
            time.sleep(10)

        except Exception as e:
            # 如果是 429 錯誤 (頻率限制)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⚠️ 觸發頻率限制，Google 要求休息。原地睡眠 30 秒後重試...")
                time.sleep(30)
                retry_count += 1
            else:
                print(f"❌ 其它錯誤: {filename} - {e}")
                break # 其它錯誤就不重試了

print("🏁 所有圖片處理程序結束。")
