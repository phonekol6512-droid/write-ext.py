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
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')
    hash_setting = request.values.get('hash_setting')

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
        return ym_read("change_default", "t-האם לשנות ברירת מחדל? 1-כן 0-לא", 1)

    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה ספרות? 1-9", 1)

    # 5. שאלת קול
    if not change_voice:
        return ym_read("change_voice", "t-לבחור קול? 1-כן 0-לא", 1)

    if change_voice == "1" and not voice_choice:
        return ym_read("voice_choice", "t-קול: 1-אליק 2-יעקב 3-סיוון 4-אסנת", 1)

    # 6. שאלת סולמית
    if not hash_setting:
        return ym_read("hash_setting", "t-הפעל סולמית? 1-כן 0-לא", 1)

    try:
        clean_ext = extension.strip().replace('*', '/').replace('-', '/').strip('/')
        if not clean_ext:
            return ym_say_and_hangup("t-שגיאה: שלוחה ריקה")

        token = f"{system.strip()}:{password.strip()}"
        digits = int(num_digits) if num_digits and num_digits.isdigit() else 1

        voice_map = {
            "1": "Elik_2100",
            "2": "Jacob",
            "3": "Sivan",
            "4": "Osnat"
        }
        selected_voice = voice_map.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"
        hash_line = "hash_extension=yes" if hash_setting == "1" else ""

        # ---------- שלב 1: יצירת השלוחה ----------
        r1 = requests.get(
            f"{YEMOT_API_URL}UpdateExtension",
            params={
                "token": token,
                "path": f"ivr2:{clean_ext}",
                "type": "menu",
                "max_digits": digits
            },
            timeout=15
        )
        print("UpdateExtension:", r1.status_code, r1.text[:100])

        if not (r1.status_code == 200 and '"responseStatus":"OK"' in r1.text):
            return ym_say_and_hangup("t-שגיאה ביצירת השלוחה")

        # ---------- שלב 2: בניית תפריט ----------
        ext_ini = f"""type=menu
title=תפריט אוטומטי
invalid=הקשת שגויה
timeout=הזמן נגמר
max_digits={digits}
{hash_line}
menu_voice={selected_voice}
default=go_to:$EXT
"""

        # ---------- שלב 3: העלאת קובץ ----------
        r2 = requests.post(
            f"{YEMOT_API_URL}UploadTextFile",
            params={
                "token": token,
                "what": f"ivr2:/{clean_ext}/ext.ini",
                "contents": ext_ini
            },
            timeout=15
        )
        print("UploadTextFile:", r2.status_code, r2.text[:100])

        # ---------- שלב 4: הודעה קצרצרה ----------
        if r2.status_code == 200 and '"responseStatus":"OK"' in r2.text:
            # הודעה ממש קצרה - רק שם השלוחה
            return ym_say_and_hangup(f"t-השלוחה {clean_ext} הוגדרה")
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאה")

    except Exception as e:
        print("Error:", str(e))
        return ym_say_and_hangup("t-שגיאה")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
