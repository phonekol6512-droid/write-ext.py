import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


def ym_response(content: str):
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str, max_digits: int = 1):
    """שאלה + המשך שיחה"""
    content = f"read={prompt}={var_name},{max_digits},12,1,Digits"
    return ym_response(content)


def ym_say_and_hangup(text: str):
    """השמעה + ניתוק"""
    content = f"id_list_message={text}\nend=true"
    return ym_response(content)


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    # קבלת כל הפרמטרים
    system       = request.values.get('system')
    password     = request.values.get('password')
    extension    = request.values.get('extension')
    change_default = request.values.get('change_default')
    num_digits   = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')

    # ==================== שלבים ====================

    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    if not change_default:
        return ym_read("change_default", "t-האם לשנות את ברירת המחדל של ההקשות? 1-כן 0-לא", 1)

    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה ספרות יקלוט התפריט? 1 עד 9", 1)

    if not change_voice:
        return ym_read("change_voice", "t-האם ברצונך לבחור קול רובוטי? 1-כן 0-לא", 1)

    if change_voice == "1" and not voice_choice:
        return ym_read("voice_choice", "t-בחר קול: 1-זכר 2-נקבה 3-מהיר. הקש 1 2 או 3", 1)

    # ==================== יצירת שלוחה ====================
    try:
        token = f"{system.strip()}:{password.strip()}"
        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

        # ערכי ברירת מחדל
        digits = int(num_digits) if num_digits and num_digits.isdigit() else 1
        voices = {"1": "he-male", "2": "he-female", "3": "he-il-2"}
        selected_voice = voices.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"

        # תוכן קובץ ext.ini
        ext_ini = f"""type=menu
title=תפריט אוטומטי
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
hash_extension=yes
menu_voice={selected_voice}
"""

        # שליחה לימות
        params = {
            "token": token,
            "what": f"ivr2:/{clean_ext}/ext.ini",
            "contents": ext_ini
        }

        r = requests.post(f"{YEMOT_API_URL}UploadTextFile", params=params, timeout=15)

        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code == 200 and '"responseStatus":"OK"' in r.text:
            summary = f"""t-השלוחה נוצרה בהצלחה!
שלוחה: {clean_ext}
הקשות: {digits}
קול: {selected_voice}
בהצלחה!"""
            return ym_say_and_hangup(summary)
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת השלוחה. בדוק את הפרטים.")

    except Exception as e:
        print("שגיאה:", str(e))
        return ym_say_and_hangup("t-אירעה שגיאה טכנית. נסה שוב.")


if __name__ == '__main__':
    print("שרת ימות המשיח פועל על http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
