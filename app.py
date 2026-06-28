import re
import logging
import requests
from flask import Flask, request, make_response

app = Flask(__name__)
YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
    # קבלת פרמטרים מהמשתמש (דרך ה-IVR)
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    num_digits = request.values.get('num_digits', '1')  # ברירת מחדל: ספרה אחת

    # שלב 1: מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # שלב 2: סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # שלב 3: מספר השלוחה החדשה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # שלב 4 (אופציונלי): כמה ספרות יקלידו?
    # אם num_digits לא הוזן, נשאל את המשתמש.
    if not num_digits:
        return ym_read("num_digits", "t-כמה ספרות יקליד המתקשר? (1-9)", 1)

    # ===================== יצירת השלוחה =====================
    try:
        # ניקוי קלט - רק ספרות
        clean_ext = re.sub(r'\D', '', extension)
        if not clean_ext:
            return ym_say_and_hangup("t-שגיאה: השלוחה חייבת להכיל ספרות בלבד.")

        token = f"{system.strip()}:{password.strip()}"
        digits = int(num_digits) if num_digits.isdigit() else 1

        # --- הרכבת הבקשה ל-UpdateExtension ---
        # הפרמטרים: token, path, type, max_digits
        # type=menu מגדיר אותה כתפריט
        # max_digits קובע כמה ספרות המתקשר יכול להקליד
        params = {
            "token": token,
            "path": f"ivr2:{clean_ext}",
            "type": "menu",
            "max_digits": digits
        }

        logging.info(f"יוצר שלוחה {clean_ext} עם {digits} ספרות")

        r = requests.get(
            f"{YEMOT_API_URL}UpdateExtension",
            params=params,
            timeout=15
        )

        logging.info(f"Status: {r.status_code}, Response: {r.text}")

        # בדיקה אם הבקשה הצליחה
        if r.status_code == 200 and '"responseStatus":"OK"' in r.text:
            return ym_say_and_hangup(
                f"t-השלוחה {clean_ext} נוצרה בהצלחה! מספר ספרות: {digits}"
            )
        else:
            logging.error(f"שגיאת API: {r.text}")
            return ym_say_and_hangup("t-שגיאה ביצירת השלוחה. בדקו את נתוני המערכת.")

    except requests.exceptions.Timeout:
        logging.error("Timeout")
        return ym_say_and_hangup("t-שגיאת תקשורת. נסו שוב.")
    except Exception as e:
        logging.exception("שגיאה כללית")
        return ym_say_and_hangup("t-שגיאה טכנית. נסו שוב.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
