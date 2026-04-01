import os
import glob
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. 初始化 (請確保 GitHub Secrets 有設定 GEMINI_API_KEY) ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

categories = {
    "上半身": ["掛脖背心", "馬甲背心", "細肩帶背心", "削肩背心", "短版T恤", "襯衫", "一字領上衣"],
    "下半身": ["熱褲", "高腰長褲", "百褶裙", "包臀裙", "牛仔長裙", "工裝褲", "瑜珈褲"],
    "連身裙": ["短版連身裙", "膝上連身裙", "過膝連身裙"],
    "外搭": ["西裝外套", "針織開衫", "牛仔夾克", "透膚襯衫", "皮衣"],
    "襪類": ["透膚黑絲", "白色長襪", "網襪", "膝上襪", "隱形襪"],
    "鞋類": ["細高跟鞋", "老爹鞋", "瑪莉珍鞋", "膝上靴", "帆布鞋", "涼鞋"],
    "風格": ["法式優雅", "性感辣妹", "清新甜美", "商務幹練", "美式街頭", "極簡冷淡", "Y2K"]
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- 2. 處理 processed_images 內的新檔案 ---
# 搜尋所有不是 [上身-下身...] 格式的原始檔案
for filepath in glob.glob("processed_images/*.*"):
    filename = os.path.basename(filepath)
    if filename == ".keep" or filename.count('-') >= 5: # 跳過已處理或特殊檔
        continue

    try:
        sample_file = genai.upload_file(path=filepath)
        prompt = f"分析穿搭並回傳格式：[上身]-[下身]-[連身裙]-[外搭]-[襪]-[鞋]_[風格]。字典：{categories}. 只回傳字串。"
        response = model.generate_content([sample_file, prompt], safety_settings=safety_settings)
        
        result = response.text.strip().replace(" ", "")
        clean_name = re.sub(r'[^\w\s-]', '', result)
        ext = os.path.splitext(filename)[1]
        
        new_path = f"processed_images/{clean_name}{ext}"
        os.rename(filepath, new_path)
        print(f"✅ 改名成功: {filename} -> {clean_name}{ext}")
    except Exception as e:
        print(f"❌ 錯誤: {filename} - {e}")
