import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://call2all.co.il"

@app.route('/write-ext', methods=['GET', 'POST'])
def write_ext_module():
    extracted = {}

    # סריקה חכמה לקריאת הגדרות קבועות מה-ext.ini (בדיוק כמו בקוד העתקות שעבד!)
    for key, value in request.values.items():
        key_str = str(key).strip()
        val_str = str(value).strip()

        if "login2" in key_str or "login2" in val_str:
            extracted['login2'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "password2" in key_str or "password2" in val_str:
            extracted['password2'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "key2" in key_str or "key2" in val_str:
            extracted['key2'] = val_str.split('=')[-1] if '=' in val_str else val_str

    # שליפת המשתנים הסופיים
    system_dst = extracted.get('login2') or request.values.get('system_dst')
    pass_dst = extracted.get('password2') or request.values.get('pass_dst')
    ext_dst = extracted.get('key2') or request.values.get('ext_dst')

    # שלבי השאלות בטלפון - ישאל אך ורק את מה שלא קיים בקובץ (ריק)
    if not system_dst or str(system_dst).strip() == "": 
        return ym_read("system_dst", "t-אנא הקישו את מספר המערכת ובסיומה סולמית")
    if not pass_dst or str(pass_dst).strip() == "":   
        return ym_read("pass_dst", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")
    if not ext_dst or str(ext_dst).strip() == "":    
        return ym_read("ext_dst", "t-אנא הקישו את מספר השלוחה להגדרה ובסיומה סולמית")

    try:
        token_dst = f"{system_dst.strip()}:{pass_dst.strip()}"
        clean_dst = ext_dst.strip().replace('*', '/').replace('-', '/').strip('/')
        path_dst = f"ivr2:/{clean_dst}/ext.ini"

        # 🎯 שתי השורות שביקשת, כולל העברית בדיוק כפי שהצלחנו להזריק בהעתקות!
         content_with_title = src_response.text + "\ntitle=שלוחה זו נבנתה על ידי מערכת פון קול"

        # 🌟 פקודת ההעלאה המקורית והמדויקת שעבדה לך פיקס, עם הציטוט התקני של פייתון! 🌟
        upload_url = f"{YEMOT_API_URL}UploadTextFile?token={token_dst}&what={path_dst}&contents={requests.utils.quote(ini_content)}"
        dst_response = requests.post(upload_url)

        if dst_response.status_code == 200 and '"responseStatus":"OK"' in dst_response.text:
            return ym_say_and_hangup("t-השלוחה הוגדרה בהצלחה כתפריט")
        return ym_say_and_hangup("t-שגיאה בהעלאת הנתונים למערכת. אנא בדוק את הפרטים.")

    except Exception as e:
        print(f"API Error: {str(e)}")
        return ym_say_and_hangup("t-התרחשה שגיאה בתקשורת עם השרתים.")

def ym_read(var_name, text):
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

def ym_say_and_hangup(text):
    res = make_response(f"id_list_message={text}")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

__all__ = ['app']
