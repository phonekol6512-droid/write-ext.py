import re
import json
import logging
import requests
from flask import Flask, request, make_response

# ===================== הגדרות בסיס =====================
app = Flask(__name__)
YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"

# לוגים (החלף את ה-print)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ===================== פונקציות עזר לתקשורת מול ימות =====================
def ym_response(content: str):
    """מחזיר תשובת HTTP תקינה עבור מנוע ימות."""
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str, max_digits=1):
    """מייצר פקודת read לקבלת קלט מהמתקשר."""
    return ym_response(f"read={prompt}={var_name},{max_digits},12,1,Digits")


def ym_say_and_hangup(text: str):
    """משמיע הודעה ומוריד את השיחה."""
    return ym_response(f"id_list_message={text}\nend=true")


# ===================== הנתיב הראשי =====================
@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    # שליפת כל הפרמטרים שהתקבלו מ-Yemot
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    change_default = request.values.get('change_default')
    num_digits = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')
    hash_setting = request.values.get('hash_setting')

    # --------------------------------------------------------
    # שלב 1: מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # שלב 2: סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # שלב 3: שלוחה חדשה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # שלב 4: שינוי ברירת מחדל של הקשות?
    if not change_default:
        return ym_read("change_default", "t-האם לשנות את מספר הספרות? 1-כן 0-לא", 1)

    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה ספרות יקליד המתקשר? (1-9)", 1)

    # שלב 5: בחירת קול רובוטי (חדש!)
    if not change_voice:
        return ym_read("change_voice", "t-לבחור קול רובוטי? 1-כן 0-לא", 1)

    if change_voice == "1" and not voice_choice:
        return ym_read("voice_choice", "t-בחר קול: 1-זכר (חדש) 2-נקבה (חדש) 3-מהיר (ישן)", 1)

    # שלב 6: הגדרת מקש סולמית (#)
    if not hash_setting:
        return ym_read("hash_setting", "t-האם מקש # ינתב לשלוחה ייעודית? 1-כן 0-לא", 1)

    # ===================== יצירת התפריט והעלאה =====================
    try:
        # ניקוי קלט – רק ספרות לשלוחה (למניעת בעיות)
        clean_ext = re.sub(r'\D', '', extension)
        if not clean_ext:
            return ym_say_and_hangup("t-שגיאה: השלוחה חייבת להכיל ספרות בלבד.")

        # בניית טוקן גישה
        token = f"{system.strip()}:{password.strip()}"

        # מספר הספרות (ברירת מחדל 1)
        digits = int(num_digits) if (num_digits and num_digits.isdigit()) else 1

        # ---------- מיפוי קולות (הגרסה החדשה!) ----------
        voice_map = {
            "1": "ymMale",      # קול גברי חדש (מנוע TTS מתקדם)
            "2": "ymFemale",    # קול נקבה חדש
            "3": "he-il-2"      # קול מהיר ישן (לגיבוי)
        }
        # ברירת מחדל: אם לא ביקשו לשנות – משתמשים בקול הרגיל (he-il-1)
        selected_voice = voice_map.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"

        # הגדרת התנהגות מקש # 
        hash_line = "hash_extension=yes" if hash_setting == "1" else ""

        # ---------- קובץ התפריט (ext.ini) ----------
        # שים לב: type=menu עם default=action:transfer $EXT – כך כל הקשה מנותבת כשלוחה
        ext_ini = f"""type=menu
title=תפריט אוטומטי
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות
max_digits={digits}
{hash_line}
menu_voice={selected_voice}
default=action:transfer $EXT
"""

        logging.info(f"מנסה להעלות קובץ לשלוחה {clean_ext} עם קול {selected_voice}")

        # שליחת הבקשה ל-API של ימות
        response = requests.post(
            f"{YEMOT_API_URL}UploadTextFile",
            params={
                "token": token,
                "what": f"ivr2:/{clean_ext}/ext.ini",
                "contents": ext_ini
            },
            timeout=15
        )

        logging.info(f"סטטוס HTTP: {response.status_code}")
        logging.info(f"תוכן התשובה: {response.text}")

        # ניתוח התשובה (JSON)
        try:
            data = response.json()
            success = (response.status_code == 200 and data.get("responseStatus") == "OK")
        except json.JSONDecodeError:
            logging.error("התשובה אינה JSON תקין")
            success = False

        if success:
            hash_status = "מופעל (פנייה לשלוחה ייעודית)" if hash_setting == "1" else "כבוי (סיום קלט)"
            return ym_say_and_hangup(
                f"t-השלוחה {clean_ext} נוצרה! ספרות: {digits}, קול: {selected_voice}, סולמית: {hash_status}"
            )
        else:
            logging.error(f"שגיאה בהעלאה: {response.text}")
            return ym_say_and_hangup("t-שגיאה בהעלאת הקובץ. אנא בדקו את נתוני המערכת.")

    except requests.exceptions.Timeout:
        logging.error("פג תוקף החיבור לשרת ימות")
        return ym_say_and_hangup("t-שגיאת תקשורת. נסו שוב מאוחר יותר.")

    except Exception as e:
        logging.exception("שגיאה כללית בלתי צפויה")
        return ym_say_and_hangup("t-שגיאה טכנית. נסו שוב.")


# ===================== הרצת השרת =====================
if __name__ == '__main__':
    # debug=True נוח לבדיקות, אבל בייצור החליפו ל-False והשתמשו ב-Gunicorn/Waitress
    app.run(host='0.0.0.0', port=5000, debug=True)
