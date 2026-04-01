import os
import glob
import re
import time
import random
import mimetypes
from google import genai
from google.genai import types

# === 基本設定 ===
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.0-flash"

# 最大重試次數
MAX_RETRY = 3

categories = {
    "上半身": ["掛脖背心", "馬甲背心", "細肩帶背心", "削肩背心", "短版T恤", "襯衫", "一字領上衣"],
    "下半身": ["熱褲", "高腰長褲", "百褶裙", "包臀裙", "牛仔長裙", "工裝褲", "瑜珈褲"],
    "連身裙": ["短版連身裙", "膝上連身裙", "過膝連身裙"],
    "外搭": ["西裝外套", "針織開衫", "牛仔夾克", "透膚襯衫", "皮衣"],
    "襪類": ["透膚黑絲", "白色長襪", "網襪", "膝上襪", "隱形襪"],
    "鞋類": ["細高跟鞋", "老爹鞋", "瑪莉珍鞋", "膝上靴", "帆布鞋", "涼鞋"],
    "風格": ["法式優雅", "性感辣妹", "清新甜美", "商務幹練", "美式街頭", "極簡冷淡", "Y2K"]
}

def safe_generate(prompt, image_part):
    """帶重試的 AI 呼叫"""
    for attempt in range(MAX_RETRY):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            image_part
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1
                )
            )

            if not response or not response.text:
                raise Exception("AI 回應為空")

            return response.text.strip()

        except Exception as e:
            print(f"⚠️ 第 {attempt+1} 次失敗: {e}")

            if attempt < MAX_RETRY - 1:
                sleep_time = random.randint(5, 15)
                print(f"⏳ 等待 {sleep_time} 秒後重試...")
                time.sleep(sleep_time)
            else:
                raise e


def get_unique_path(base_path):
    """避免檔名重複"""
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_path)
    counter = 1

    while True:
        new_path = f"{name}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


for filepath in glob.glob("processed_images/*.*"):
    filename = os.path.basename(filepath)

    # 跳過已處理
    if filename == ".keep" or filename.count('-') >= 5:
        continue

    try:
        print(f"🔍 分析中: {filename}")

        with open(filepath, "rb") as f:
            img_data = f.read()

        # 自動判斷圖片格式
        mime_type = mimetypes.guess_type(filepath)[0] or "image/jpeg"

        image_part = types.Part.from_bytes(
            data=img_data,
            mime_type=mime_type
        )

        prompt = f"""
辨識穿搭並回傳格式：
[上身]-[下身]-[連身裙]-[外搭]-[襪]-[鞋]_[風格]

限制：
- 必須從字典選
- 沒有就填 無
- 僅回傳字串

字典：
{categories}
"""

        # 🚀 呼叫 AI（含重試）
        result = safe_generate(prompt, image_part)

        result = result.replace(" ", "")

        # 清理非法字元
        clean_name = re.sub(r'[\\/:*?"<>|]', '', result)

        if not clean_name:
            raise Exception("檔名為空")

        ext = os.path.splitext(filename)[1]
        new_path = f"processed_images/{clean_name}{ext}"

        # 🚫 防撞名
        new_path = get_unique_path(new_path)

        os.rename(filepath, new_path)

        print(f"✅ 改名成功: {os.path.basename(new_path)}")

        # 💤 防 429（隨機間隔）
        sleep_time = random.randint(8, 18)
        print(f"⏳ 冷卻 {sleep_time} 秒")
        time.sleep(sleep_time)

    except Exception as e:
        print(f"❌ 錯誤: {filename} - {e}")
