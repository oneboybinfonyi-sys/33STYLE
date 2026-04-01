import os
import glob
import re
import time
from google import genai
from google.genai import types

# --- 2026 標準初始化 ---
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

# 處理照片
for filepath in glob.glob("processed_images/*.*"):
    filename = os.path.basename(filepath)
    if filename == ".keep" or filename.count('-') >= 5:
        continue

    try:
        print(f"正在分析: {filename}...")
        with open(filepath, "rb") as f:
            img_data = f.read()
        
        image = types.Part.from_bytes(data=img_data, mime_type="image/jpeg")
        prompt = f"辨識穿搭並回傳格式：[上身]-[下身]-[連身裙]-[外搭]-[襪]-[鞋]_[風格]。字典：{categories}. 僅回傳字串。"
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                safety_settings=[types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE")],
                temperature=0.1
            )
        )
        
        result = response.text.strip().replace(" ", "")
        clean_name = re.sub(r'[^\w\s-]', '', result)
        ext = os.path.splitext(filename)[1]
        
        new_path = f"processed_images/{clean_name}{ext}"
        os.rename(filepath, new_path)
        print(f"✅ 改名成功: {clean_name}")

        # 🕒 關鍵：為了避開 429 錯誤，每張圖強制休息 30 秒
        print("等待 30 秒避開頻率限制...")
        time.sleep(30)

    except Exception as e:
        if "429" in str(e):
            print("⚠️ 觸發 Google 限制，本次任務終止，請等 1 分鐘後再試。")
            break
        print(f"❌ 錯誤: {e}")
