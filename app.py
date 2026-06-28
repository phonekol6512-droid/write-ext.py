import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


def ym_response(content: str):
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str, max_digits=1):
    return ym_response(f"read={prompt}={var_name},{max_digits},12,1,Digits")


def ym_say_and_hangup(text: str):
    return ym_response(f"id_list_message={text}\nend=true")


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    print("=== בקשה חדשה ===")
    print(request.values.to_dict())

    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    change_default = request.values.get('change_default')
    num_digits = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')
    hash_setting = request.values.get('hash_setting')

    # אם יש את כל הפרמטרים - יצירה
    if system and password and extension and change_default and hash_setting:
        print("כל הפרמטרים קיימים - מתחיל יצירה")
        try:
            token = f"{system.strip()}:{password.strip()}"
            clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

            digits = int(num_digits) if num_digits and num_digits.isdigit() else 1
            voices = {"1": "he-male", "2": "he-female", "3": "he-il-2"}
            selected_voice = voices.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"
            hash_line = "hash_extension=yes" if hash_setting == "1" else ""

            ext_ini = f"""type=menu
title=תפריט אוטומטי
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
{hash_line}
menu_voice={selected_voice}
"""

            # יצירת שלוחה
            requests.post(f"{YEMOT_API_URL}UpdateExtension", params={
                "token": token,
                "ext": clean_ext,
                "name": f"תפריט {clean_ext}",
                "type": "ivr"
            }, timeout=10)

            # העלאת ext.ini
            r = requests.post(f"{YEMOT_API_URL}UploadTextFile", params={
                "token": token,
                "what": f"ivr2:/{clean_ext}/ext.ini",
                "contents": ext_ini
            }, timeout=15)

            print("Upload Status:", r.status_code)
            print("Response:", r.text)

            if r.status_code == 200 and '"responseStatus":"OK"' in r.text:
                return ym_say_and_hangup(f"t-השלוחה {clean_ext} נוצרה בהצלחה!")
            else:
                return ym_say_and_hangup("t-שגיאה בהעלאה.")

        except Exception as e:
            print("שגיאה:", str(e))
            return ym_say_and_hangup("t-שגיאה.")

    # שאלות
    if not system: return ym_read("system", "t-מערכת?", 10)
    if not password: return ym_read("password", "t-סיסמה?", 10)
    if not extension: return ym_read("extension", "t-שלוחה?", 10)
    if not change_default: return ym_read("change_default", "t-שנות ברירת מחדל? 1-כן 0-לא", 1)
    if change_default == "1" and not num_digits: return ym_read("num_digits", "t-כמה ספרות?", 1)
    if not change_voice: return ym_read("change_voice", "t-קול רובוטי? 1-כן 0-לא", 1)
    if change_voice == "1" and not voice_choice: return ym_read("voice_choice", "t-בחר קול 1 2 3", 1)
    if not hash_setting: return ym_read("hash_setting", "t-# כשלוחה? 1-כן 0-לא", 1)

    return ym_say_and_hangup("t-שגיאה.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
