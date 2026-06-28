import requests
from flask import Flask, request, make_response
import urllib.parse

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


def ym_response(content: str):
    """עוזר לבנות תשובה תקינה לימות"""
    res = make_response(content)
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_read(var_name: str, prompt: str):
    """השמעה + קליטת הקשה"""
    content = f"read={prompt}={var_name},4,12,1,Digits"
    return ym_response(content)


def ym_say_and_hangup(text: str):
    """השמעה + סיום שיחה"""
    content = f"id_list_message={text}\nend=true"
    return ym_response(content)


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():
    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')

    # שלב 1: קליטת מספר מערכת
    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית")

    # שלב 2: קליטת סיסמה
    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")

    # שלב 3: קליטת מספר שלוחה
    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה ובסיומה סולמית")

    try:
        token = f"{system.strip()}:{password.strip()}"
        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")
        
        # בניית תוכן ext.ini
        ext_ini = f"""type=menu
title=תפריט שנבנה אוטומטית
invalid=הקשת שגויה, נסה שוב
timeout=הזמן נגמר, להתראות

1=go_to:some_folder
2=play:ברוך הבא לשירות
#=go_to:main
"""

        # העלאת הקובץ
        upload_url = f"{YEMOT_API_URL}UploadTextFile"
        
        params = {
            "token": token,
            "what": f"ivr2:/{clean_ext}/ext.ini",
            "contents": ext_ini
        }

        response = requests.post(upload_url, params=params, timeout=15)
        
        print("Status Code:", response.status_code)
        print("Response:", response.text)

        if response.status_code == 200 and '"responseStatus":"OK"' in response.text:
            return ym_say_and_hangup("t-השלוחה נוצרה בהצלחה! תודה.")
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת הקובץ. בדוק את הפרטים.")

    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
        return ym_say_and_hangup("t-שגיאת תקשורת עם שרת ימות.")
    except Exception as e:
        print("General Error:", e)
        return ym_say_and_hangup("t-אירעה שגיאה לא צפויה.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
