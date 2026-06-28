import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://call2all.co.il"

@app.route('/write-ext', methods=['GET', 'POST'])
def write_ext_module():
    system_dst = request.values.get('system_dst')
    pass_dst = request.values.get('pass_dst')
    ext_dst = request.values.get('ext_dst')

    if not system_dst: 
        return ym_read("system_dst", "t-אנא הקישו את מספר המערכת ובסיומה סולמית")
    if not pass_dst:   
        return ym_read("pass_dst", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")
    if not ext_dst:    
        return ym_read("ext_dst", "t-אנא הקישו את מספר השלוחה להגדרה ובסיומה סולמית")

    try:
        token_dst = f"{system_dst.strip()}:{pass_dst.strip()}"
        clean_dst = ext_dst.strip().replace('*', '/').replace('-', '/').strip('/')
        
        # 🌟 הקידוד המנצח: שתי השורות מומרות מראש לטקסט אינטרנט בטוח ללא אותיות בעברית בקוד!
        encoded_ini = "type%3Dmenu%0Atitle%3D%D7%A0%D7%91%D7%A0%D7%94%20%D7%91%D7%90%D7%91%D7%A5%D7%A2%D7%95%D7%AA%20%D7%A4%D7%95%D7%9F%20%D7%A7%D7%95%D7%9C"

        # שליחה ישירה ב-URL בדיוק כמו שימות המשיח מחייבת
        upload_url = f"{YEMOT_API_URL}CustomCreate?token={token_dst}&path=ivr2:/{clean_dst}&ini={encoded_ini}"
        dst_response = requests.post(upload_url)

        # בדיקה אם ימות המשיח אישרה את יצירת השלוחה
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
