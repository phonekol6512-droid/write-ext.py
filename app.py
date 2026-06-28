import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():

    system = request.values.get('system')
    password = request.values.get('password')
    extension = request.values.get('extension')

    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית")

    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")

    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה ובסיומה סולמית")

    try:

        token = f"{system.strip()}:{password.strip()}"

        clean_ext = extension.strip().replace("*", "/").replace("-", "/").strip("/")

        path = f"ivr2:/{clean_ext}/ext.ini"

        ext_ini = """type=menu
title=נבנה באמצעות פון קול"""

        upload_url = (
            f"{YEMOT_API_URL}UploadTextFile"
            f"?token={token}"
            f"&what={path}"
            f"&contents={requests.utils.quote(ext_ini)}"
        )

        response = requests.post(upload_url)

        print(response.status_code)
        print(response.text)

        if response.status_code == 200 and '"responseStatus":"OK"' in response.text:
            return ym_say_and_hangup("t-השלוחה הוגדרה בהצלחה")

        return ym_say_and_hangup("t-אירעה שגיאה ביצירת השלוחה")

    except Exception as e:
        print(e)
        return ym_say_and_hangup("t-אירעה שגיאה בתקשורת עם השרת")


def ym_read(var_name, text):
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_say_and_hangup(text):
    res = make_response(
        f"id_list_message={text}\n"
        f"hangup=yes"
    )
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


__all__ = ["app"]
