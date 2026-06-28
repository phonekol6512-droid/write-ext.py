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

    # 1. מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית", 10)

    # 2. סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית", 10)

    # 3. שלוחה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה החדשה ובסיומה סולמית", 10)

    # 4. שינוי ברירת מחדל של הקשות
    if not change_default:
        return ym_read("change_default", "t-האם אתה רוצה לשנות את ברירת המחדל של ההקשות? 1-כן 0-לא", 1)

    if change_default == "1" and not num_digits:
        return ym_read("num_digits", "t-כמה הקשות (ספרות) ברצונך? (1-9)", 1)

    # 5. האם לבחור קול רובוטי
    if not change_voice:
        return ym_read("change_voice", "t-האם ברצונך לבחור קול רובוטי? 1-כן 0-לא", 1)

    # 6. בחירת הקול (רק אם בחר 
