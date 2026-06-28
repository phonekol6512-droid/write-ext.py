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
    change_default = request.values.get('change_default')
    num_digits = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')   # 1 = כן, 0 = לא
    voice_choice = request.values.get('voice_choice')   # בחירת קול

    # 1. מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # 2. סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # 3. מספר שלוחה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # 4. האם לשנות ברירת מחדל של הקשות
    if not change_default:
        prompt = "t-האם אתה רוצה לשנות את ברירת המחדל של ההקשות? הקש 1 לשינוי, 0 להמשיך ללא שינוי"
        return ym_read("change_default", prompt, 1)

    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה הקשות (ספרות) ברצונך שיהיו בתפריט? (1-9)", 1)

    # 5. האם לבחור קול רובוטי
    if not change_voice:
        prompt = "t-האם ברצונך לבחור קול רובוטי להודעות התפריט? הקש 1 לבחירה, 0 להמשיך עם ברירת המחדל"
        return ym_read("change_voice", prompt, 1)

    # 6. בחירת הקול (אם בחר 1)
    if change_voice == "1" and not voice_choice:
        prompt = "t-בחר קול: 1-קול זכר, 2-קול נקבה, 3-קול מהיר. הקש את המספר"
        return ym_read("voice_choice", prompt, 1)

    try:
        token = f"{system.strip()}:{password.strip()}"
        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

        digits = int(num_digits) if num_digits and num_digits.isdigit() else 1

        # בחירת קול
        voices = { "1": "he-male", "2": "he-female", "3": "he-il-2" }
        selected_voice = voices.get(voice_choice, "he-il-1")   # ברירת מחדל

        # בניית ext.ini
        ext_ini = f"""type=menu
title=תפריט שנבנה אוטומטית
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
hash_extension=yes
menu_voice={selected_voice}
"""

        # העלאה
        upload_url = f"{YEMOT_API_URL}UploadTextFile"
        params = {
            "token": token,
            "what": f"ivr2:/{clean_ext}/ext.ini",
            "contents": ext_ini
        }

        response = requests.post(upload_url, params=params, timeout=15)

        if response.status_code == 200 and '"responseStatus":"OK"' in response.text:
            summary = f"""t-הכל מוכן בהצלחה!
שלוחה: {clean_ext}
הקשות: {digits}
קול רובוטי: {selected_voice}
בהצלחה רבה!"""
            return ym_say_and_hangup(summary)
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת השלוחה.")

    except Exception as e:
        print("Error:", str(e))
        return ym_say_and_hangup("t-אירעה שגיאה. נסה שוב.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
