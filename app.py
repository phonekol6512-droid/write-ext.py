import requests
from flask import Flask, request, make_response
import urllib.parse

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
    # קבלת המשתנים מהשיחה
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    default_digits = request.values.get('default_digits')   # כמה ספרות בברירת מחדל
    confirm = request.values.get('confirm')                 # 1 = אישור, 0 = שינוי

    # שלב 1: מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # שלב 2: סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # שלב 3: מספר שלוחה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # שלב 4: ברירת מחדל - כמה ספרות
    if not default_digits:
        return ym_read("default_digits", "t-כמה ספרות ברירת מחדל יקלוט התפריט? (למשל 1 או 2)", 2)

    # שלב 5: אישור או שינוי
    if not confirm:
        return ym_read("confirm", "t-ברירת המחדל היא " + default_digits + " ספרות. להמשיך? הקש 1 לאישור, 0 לשינוי", 1)

    try:
        token = f"{system.strip()}:{password.strip()}"
        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

        # אם לא אישר - חוזר לשאול כמה ספרות
        if confirm == "0":
            return ym_read("default_digits", "t-כמה ספרות ברצונך שהתפריט יקלוט? (1-9)", 1)

        num_digits = int(default_digits) if default_digits.isdigit() else 1

        # בניית ext.ini משודרג
        ext_ini = f"""type=menu
title=תפריט שנבנה אוטומטית
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={num_digits}
hash_extension=yes

1=go_to:option1
2=go_to:option2
3=go_to:option3
#=go_to:main
"""

        # העלאה לשרת
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
            return ym_say_and_hangup(f"t-השלוחה {clean_ext} נוצרה בהצלחה! ברירת מחדל: {num_digits} ספרות.")
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת השלוחה. בדוק את הפרטים.")

    except Exception as e:
        print("Error:", e)
        return ym_say_and_hangup("t-אירעה שגיאה. נסה שוב.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
