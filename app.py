import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"


@app.route('/create-menu', methods=['GET', 'POST'])
def create_menu():

    system = request.values.get("system")
    password = request.values.get("password")
    extension = request.values.get("extension")

    change_digits = request.values.get("change_digits")
    digits = request.values.get("digits")

    if not system:
        return ym_read("system", "t-אנא הקישו את מספר המערכת ובסיומה סולמית")

    if not password:
        return ym_read("password", "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")

    if not extension:
        return ym_read("extension", "t-אנא הקישו את מספר השלוחה ובסיומה סולמית")


    # -------------------------
    # מספר ספרות
    # -------------------------

    if change_digits is None:
        return ym_read(
            "change_digits",
            "t-ברירת המחדל היא תפריט בעל ספרה אחת. להשארת ברירת המחדל הקישו 0. לשינוי הקישו 1",
            1,
            1
        )

    if change_digits == "1" and not digits:
        return ym_read(
            "digits",
            "t-אנא הקישו את מספר הספרות הרצוי",
            1,
            2
        )


    # -------------------------
    # בניית ext.ini
    # -------------------------

    ext = []

    ext.append("type=menu")
    ext.append("title=נבנה באמצעות פון קול")

    if change_digits == "0":
        ext.append("digits=1")
    else:
        ext.append(f"digits={digits}")


    ext_ini = "\n".join(ext)


    token = f"{system.strip()}:{password.strip()}"

    clean = extension.strip().replace("*", "/").replace("-", "/").strip("/")

    path = f"ivr2:/{clean}/ext.ini"

    upload_url = (
        f"{YEMOT_API_URL}UploadTextFile"
        f"?token={token}"
        f"&what={path}"
        f"&contents={requests.utils.quote(ext_ini)}"
    )

    try:

        r = requests.post(upload_url, timeout=30)

        print(r.status_code)
        print(r.text)

        if r.status_code == 200 and "OK" in r.text:
            return ym_say("t-השלוחה הוגדרה בהצלחה")

        return ym_say("t-אירעה שגיאה ביצירת השלוחה")

    except Exception as e:

        print(e)

        return ym_say("t-שגיאת תקשורת")


def ym_read(var_name, text, min_digits=1, max_digits=12):

    res = make_response(
        f"read={text}={var_name},{min_digits},{max_digits},1,Digits"
    )

    res.headers["Content-Type"] = "text/plain; charset=utf-8"

    return res


def ym_say(text):

    res = make_response(f"id_list_message={text}")

    res.headers["Content-Type"] = "text/plain; charset=utf-8"

    return res


__all__ = ["app"]
