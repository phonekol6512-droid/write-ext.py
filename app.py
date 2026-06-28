import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


def ym_response(content: str):
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str, max_digits=1):
    content = f"read={prompt}={var_name},{max_digits},12,1,Digits"
    return ym_response(content)


def ym_say_and_hangup(text: str):
    content = f"id_list_message={text}\nend=true"
    return ym_response(content)


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    change_default = request.values.get('change_default')   # 1 = כן לשנות, 0 = לא
    num_digits = request.values.get('num_digits')           # כמות ההקשות אם בחר לשנות

    # 1. מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # 2. סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # 3. מספר שלוחה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # 4. שאלת שינוי ברירת מחדל
    if not change_default:
        prompt = "t-האם אתה רוצה לשנות את ברירת המחדל של ההקשות? הקש 1 לשינוי, 0 להמשיך ללא שינוי"
        return ym_read("change_default", prompt, 1)

    # 5. אם בחר לשנות - שואל כמה ספרות
    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה הקשות (ספרות) ברצונך שיהיו בתפריט? (1-9)", 1)

    try:
        token = f"{system.strip()}:{password.strip()}"
        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

        # קביעת כמות הספרות
        digits = int(num_digits) if num_digits and num_digits.isdigit() else 1

        # בניית ext.ini
        ext_ini = f"""type=menu
title=תפריט שנבנה אוטומטית
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
hash_extension=yes

1=go_to:option1
2=go_to:option2
3=go_to:option3
#=go_to:main
"""

        # העלאה לימות
        upload_url = f"{YEMOT_API_URL}UploadTextFile"
        params = {
            "token": token,
            "what": f"ivr2:/{clean_ext}/ext.ini",
            "contents": ext_ini
        }

        response = requests.post(upload_url, params=params, timeout=15)
        
        print("Status:", response.status_code)
        print("Response:", response.text)

        if response.status_code == 200 and '"responseStatus":"OK"' in response.text:
            return ym_say_and_hangup(f"t-השלוחה {clean_ext} נוצרה בהצלחה!פרטי התפריט ברירת מחדל: {digits} ספרות.")
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת השלוחה.")

    except Exception as e:
        print("Error:", str(e))
        return ym_say_and_hangup("t-אירעה שגיאה. נסה שוב.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
