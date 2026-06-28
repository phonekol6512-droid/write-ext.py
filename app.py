import re
import json
import logging
import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"

# הגדרת לוגים (מחליף את ה-print הפשוט)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def ym_response(content: str):
    """עוטף טקסט בתשובת HTTP תקינה לימות."""
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str, max_digits=1):
    """מחזיר פקודת read לשאילת משתנה מהמתקשר."""
    return ym_response(f"read={prompt}={var_name},{max_digits},12,1,Digits")


def ym_say_and_hangup(text: str):
    """משמיע הודעה ומוריד את השיחה."""
    return ym_response(f"id_list_message={text}\nend=true")


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    # שליפת כל הפרמטרים מהקריאה של ימות
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    change_default = request.values.get('change_default')
    num_digits = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')
    hash_setting = request.values.get('hash_setting')

    # פונקציית עזר פנימית לבדיקת ביטול (*)
    def check_cancel(value):
        if value == "*":
            return ym_say_and_hangup("t-ביטול הפעולה. להתראות.")
        return None

    # שלב 1–3: איסוף פרטי מערכת, סיסמה ושלוחה
    if not system:
        cancel_res = check_cancel(system)
        if cancel_res:
            return cancel_res
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    if not password:
        cancel_res = check_cancel(password)
        if cancel_res:
            return cancel_res
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    if not extension:
        cancel_res = check_cancel(extension)
        if cancel_res:
            return cancel_res
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # שלב 4: בחירת אופן הקשות (ברירת מחדל או מספר ספרות מותאם)
    if not change_default:
        cancel_res = check_cancel(change_default)
        if cancel_res:
            return cancel_res
        return ym_read("change_default", "t-האם לשנות ברירת מחדל של הקשות? 1-כן 0-לא", 1)

    if change_default == "1" and not num_digits:
        cancel_res = check_cancel(num_digits)
        if cancel_res:
            return cancel_res
        return ym_read("num_digits", "t-כמה ספרות יקליד המתקשר? (1-9)", 1)

    # שלב 5: בחירת קול
    if not change_voice:
        cancel_res = check_cancel(change_voice)
        if cancel_res:
            return cancel_res
        return ym_read("change_voice", "t-לבחור קול רובוטי? 1-כן 0-לא", 1)

    if change_voice == "1" and not voice_choice:
        cancel_res = check_cancel(voice_choice)
        if cancel_res:
            return cancel_res
        return ym_read("voice_choice", "t-בחר קול: 1-זכר 2-נקבה 3-מהיר", 1)

    # שלב 6: הגדרת מקש סולמית (#)
    if not hash_setting:
        cancel_res = check_cancel(hash_setting)
        if cancel_res:
            return cancel_res
        return ym_read("hash_setting", "t-האם מקש # ינתב לשלוחה ייעודית? 1-כן 0-לא (סיום קלט)", 1)

    # ================ יצירת קובץ התפריט ================
    try:
        # ניקוי השלוחה – רק ספרות (מניעת התקפות Path Traversal)
        clean_ext = re.sub(r'\D', '', extension)
        if not clean_ext:
            return ym_say_and_hangup("t-שגיאה: השלוחה חייבת להכיל ספרות בלבד.")

        token = f"{system.strip()}:{password.strip()}"

        # כמות הספרות שהמתקשר יקליד
        digits = int(num_digits) if (num_digits and num_digits.isdigit()) else 1

        # מיפוי קולות
        voices = {"1": "he-male", "2": "he-female", "3": "he-il-2"}
        selected_voice = voices.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"

        # הגדרת הסולמית
        hash_line = "hash_extension=yes" if hash_setting == "1" else ""

        # ------------------- תיקון קריטי! -------------------
        # שימוש ב-type=regex כדי לאפשר למתקשר לחייג כל מספר,
        # והמערכת תנתב אותו אוטומטית לשלוחה שהקיש.
        # (זה פותר את הבעיה שבה לא היה שום מיפוי למקשים)
        ext_ini = f"""type=regex
title=תפריט אוטומטי
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
regex_pattern=^([0-9]{{1,{digits}}})$
default=action:transfer ${{REGEX1}}
{hash_line}
menu_voice={selected_voice}
"""
        logging.info(f"יוצר תפריט לשלוחה {clean_ext} עם {digits} ספרות, קול {selected_voice}")

        # העלאת הקובץ לשרתי ימות
        r = requests.post(
            f"{YEMOT_API_URL}UploadTextFile",
            params={
                "token": token,
                "what": f"ivr2:/{clean_ext}/ext.ini",
                "contents": ext_ini
            },
            timeout=15
        )

        logging.info(f"סטטוס העלאה: {r.status_code}")

        # קריאת התשובה כ-JSON (בטוחה יותר)
        try:
            response_data = r.json()
            logging.info(f"תשובת השרת: {response_data}")
            is_success = (r.status_code == 200 and response_data.get("responseStatus") == "OK")
        except json.JSONDecodeError:
            logging.error(f"תשובה לא תקינה (לא JSON): {r.text}")
            is_success = False

        if is_success:
            hash_status = "מופעל (פנייה לשלוחה ייעודית)" if hash_setting == "1" else "כבוי (סיום קלט)"
            return ym_say_and_hangup(
                f"t-השלוחה {clean_ext} נוצרה בהצלחה! "
                f"מספר ספרות: {digits}, קול: {selected_voice}, סולמית: {hash_status}"
            )
        else:
            logging.error(f"שגיאת API: {r.text}")
            return ym_say_and_hangup("t-שגיאה בהעלאת הקובץ. בדקו את הסיסמה והמערכת.")

    except requests.exceptions.Timeout:
        logging.error("Timeout בהתחברות ל-API של ימות")
        return ym_say_and_hangup("t-שגיאת תקשורת. נסו שוב מאוחר יותר.")
    except Exception as e:
        logging.exception("שגיאה כללית:")  # מדפיס את הפיל המלא ללוג
        return ym_say_and_hangup("t-שגיאה טכנית. נסו שוב.")


if __name__ == '__main__':
    # חשוב! debug=False בסביבת ייצור (ודאו שמשתני הסביבה מוגדרים)
    # מומלץ להריץ עם Gunicorn או Waitress במקום ה-Server המובנה.
    app.run(host='0.0.0.0', port=5000, debug=False)
