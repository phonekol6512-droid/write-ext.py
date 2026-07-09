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


def ym_say_and_return(text: str):
    """משמיע הודעה וחוזר לתפריט הראשי."""
    return ym_response(f"id_list_message={text}\nend_goto=/")


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')
    change_default = request.values.get('change_default')
    num_digits = request.values.get('num_digits')
    change_voice = request.values.get('change_voice')
    voice_choice = request.values.get('voice_choice')
    change_speed = request.values.get('change_speed')
    speed_choice = request.values.get('speed_choice')
    omer_choice = request.values.get('omer_choice')
    conf_bridge = request.values.get('conf_bridge')
    conf_extension = request.values.get('conf_extension')
    hash_setting = request.values.get('hash_setting')
    star_setting = request.values.get('star_setting')

    # ---------- שלב 1: מספר מערכת ----------
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיום הקישו סולמית", 10)

    # ---------- שלב 2: סיסמה ----------
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיום הקישו סולמית", 10)

    # ---------- שלב 3: מספר שלוחה ----------
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה ובסיום הקישו סולמית, לשלוחה פנימית הקישו כוכבית בין שלוחה לשלוחה", 10)

    # ---------- שלב 4: שינוי ברירת מחדל של הקשות ----------
    if not change_default:
        return ym_read("change_default", "t-ברירת מחדל לכל שלוחה יש סיפרה אחת בלבד וכשמקישים 1 אז נכנסים לשלוחה 1 ואם מקישים 2 אז נכנסים לשלוחה 2, לשינוי הקישו 1 וסולמית להמשך ללא שינוי הקישו 0", 1)
    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-אנא הקישו את מספר ההקשות בסיום הקישו סולמית", 1)

    # ---------- שלב 5: בחירת קול ----------
    if not change_voice:
        return ym_read("change_voice", "t-האם ברצונך להגדיר את הקול הרובוטי בשלוחה, להגדרה הקישו 1 וסולמית להמשך ללא שינוי הקישו 0 וסולמית", 1)
    if change_voice == "1" and not voice_choice:
        return ym_read("voice_choice", "t-בחר קול:  לאליק הקישו 1 וסולמית ליעקב הקישו 2 וסולמית לסיוון הקישו 3 וסולמית לאסנת הקישו 4 וסולמית", 1)

    # ---------- שלב 6: מהירות הקריאה ----------
    if not change_speed:
        return ym_read("change_speed", "t-האם ברצונך לשנות את מהירות הקול הרובוטי? לשינוי הקישו 1 וסולמית להמשך ללא שינוי הקישו 0 וסולמית", 1)
    if change_speed == "1" and not speed_choice:
        return ym_read("speed_choice", "t-בחר מהירות: לקול קצת איטי הקש 1, לקול צת מהיר הקש 2, לקול איטי הקש 3, לקול מהיר הקש 4, לקול איטי מאוד הקש 5, לקול מהיר מאוד הקש 6, לקול איטי במיוחד הקש 7, לקול מהיר במיוחד הקש 8", 1)

    # ---------- שלב 7: ספירת העומר ----------
    if omer_choice is None:
        return ym_read("omer_choice", "t-האם להפעיל בתפריט תזכורת ספירת העומר? להפעלה הקישו 1 וסולמית לביטול הקישו 0 וסולמית", 1)

    # ---------- שלב 8: הודעת ועידה פעילה ----------
    if conf_bridge is None:
        return ym_read("conf_bridge", "t-האם ברצונך להפעיל הודעה שמודיעה אם קיימת ועידה פעילה? להפעלה הקישו 1 וסולמית לביטול הקישו 0 וסולמית", 1)
    if conf_bridge == "1" and not conf_extension:
        return ym_read("conf_extension", "t-אנא הקישו את מספר השלוחה של חדר הועידה ובסיום הקישו סולמית לשלוחה פנימית הקישו כוכבית בין שלוחה לשלוחה", 10)

    # ---------- שלב 9: מקש סולמית # ----------
    if not hash_setting:
        return ym_read("hash_setting", "t-ברירת המחדל מקש סולמית משמש לחזרה לתפריט הקודם, אם ברצונך ששלוחה סולמית תיהיה שלוחה בפני עצמה הקישו 1 וסולמית להמשך ללא שינוי הקישו 0 וסולמית", 1)

    # ---------- שלב 10: מקש כוכבית * ----------
    if star_setting is None:
        return ym_read("star_setting", "t-ברירת המחדל מקש כוכבית משמש כמקש חזרה לתפריט הראשי, אם ברצונך ששלוחת כוכבית תיהיה שלוחה בפני עצמה הקישו 1 וסולמית להמשך ללא שינוי הקישו 0 וסולמית", 1)

    # ===================== יצירת השלוחה =====================
    try:
        clean_ext = extension.strip().replace('*', '/').replace('-', '/').strip('/')
        if not clean_ext:
            return ym_say_and_return("t-שגיאה: השלוחה ריקה")

        token = f"{system.strip()}:{password.strip()}"
        digits = int(num_digits) if (num_digits and num_digits.isdigit()) else 1

        voice_map = {
            "1": "Elik_2100",
            "2": "Jacob",
            "3": "Sivan",
            "4": "Osnat"
        }
        selected_voice = voice_map.get(voice_choice, "he-il-1") if change_voice == "1" else "he-il-1"

        speed_map = {
            "1": "-2", "2": "2", "3": "-4", "4": "4",
            "5": "-7", "6": "7", "7": "-10", "8": "10"
        }
        selected_speed = speed_map.get(speed_choice, "0") if change_speed == "1" else "0"

        omer_line = "omer_today_play=yes" if omer_choice == "1" else ""
        conf_lines = ""
        if conf_bridge == "1" and conf_extension:
            conf_lines = f"menu_say_conf_bridge=yes\nmenu_say_conf_bridge_1={conf_extension.strip()}"
        hash_line = "hash_extension=yes" if hash_setting == "1" else ""
        star_line = "star_extension=yes" if star_setting == "1" else ""

        ext_ini = f"""type=menu
title=שלוחת תפריט נבנה באמצעות מגדיר פון 
max_digits={digits}
{hash_line}
{star_line}
menu_voice={selected_voice}
rate={selected_speed}
{omer_line}
{conf_lines}
default=go_to:$EXT
"""

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
        logging.info(f"UpdateExtension: {r1.status_code} - {r1.text}")

        if not (r1.status_code == 200 and '"responseStatus":"OK"' in r1.text):
            return ym_say_and_return("t-שגיאה ביצירת השלוחה")

        # ---------- שלב 2: העלאת קובץ התפריט ----------
        r2 = requests.post(
            f"{YEMOT_API_URL}UploadTextFile",
            params={
                "token": token,
                "what": f"ivr2:/{clean_ext}/ext.ini",
                "contents": ext_ini
            },
            timeout=15
        )
        logging.info(f"UploadTextFile: {r2.status_code} - {r2.text}")

        # ---------- שלב 3: הודעת סיכום (מובטחת) ----------
        if r2.status_code == 200 and '"responseStatus":"OK"' in r2.text:
            speed_labels = {
                "-2": "קצת איטי", "2": "קצת מהיר", "-4": "איטי",
                "4": "מהיר", "-7": "איטי מאוד", "7": "מהיר מאוד",
                "-10": "איטי במיוחד", "10": "מהיר במיוחד"
            }
            speed_label = speed_labels.get(selected_speed, "רגיל")
            omer_status = "פעיל" if omer_choice == "1" else "כבוי"
            conf_status = f"פעיל ({conf_extension})" if conf_bridge == "1" else "כבוי"
            hash_status = "נפרד" if hash_setting == "1" else "ברירת מחדל"
            star_status = "נפרד" if star_setting == "1" else "ברירת מחדל"
            msg = (f"t-השלוחה {clean_ext} הוגדרה. מהירות: {speed_label}. "
                   f"עומר: {omer_status}. ועידה: {conf_status}. "
                   f"סולמית: {hash_status}. כוכבית: {star_status}")
            return ym_say_and_return(msg)  # הודעה + חזרה לתפריט הראשי
        else:
            return ym_say_and_return("t-השלוחה נוצרה אך התפריט לא נטען")

    except Exception as e:
        logging.exception("שגיאה")
        return ym_say_and_return("t-שגיאה טכנית. נסה שוב")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
