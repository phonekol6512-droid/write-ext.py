import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://call2all.co.il/UploadTextFile"


@app.route("/write-ext", methods=["GET", "POST"])
def write_ext_module():

    # קבלת הפרמטרים
    system_dst = request.values.get("system_dst")
    pass_dst = request.values.get("pass_dst")
    ext_dst = request.values.get("ext_dst")

    # שאלות למשתמש
    if not system_dst:
        return ym_read(
            "system_dst",
            "t-אנא הקישו את מספר המערכת ובסיומה סולמית"
        )

    if not pass_dst:
        return ym_read(
            "pass_dst",
            "t-אנא הקישו את סיסמת המערכת ובסיומה סולמית"
        )

    if not ext_dst:
        return ym_read(
            "ext_dst",
            "t-אנא הקישו את מספר השלוחה להגדרה ובסיומה סולמית"
        )

    try:

        token = f"{system_dst.strip()}:{pass_dst.strip()}"

        clean_ext = (
            ext_dst.strip()
            .replace("*", "/")
            .replace("-", "/")
            .strip("/")
        )

        path = f"ivr2:/{clean_ext}/ext.ini"

        ini_content = (
            "type=menu\n"
            "title=נבנה באמצעות פון קול"
        )

        payload = {
            "token": token,
            "what": path,
            "contents": ini_content
        }

        response = requests.post(
            YEMOT_API_URL,
            data=payload,
            timeout=30
        )

        print("========== Upload ==========")
        print("URL:", YEMOT_API_URL)
        print("Payload:", payload)
        print("Status:", response.status_code)
        print("Response:", response.text)
        print("============================")

        if response.status_code != 200:
            return ym_say_and_hangup(
                "t-שרת ימות המשיח החזיר שגיאה"
            )

        try:
            result = response.json()
        except Exception:
            return ym_say_and_hangup(
                "t-התקבלה תשובה לא תקינה מהשרת"
            )

        if result.get("responseStatus") == "OK":
            return ym_say_and_hangup(
                "t-השלוחה הוגדרה בהצלחה כתפריט"
            )

        return ym_say_and_hangup(
            f't-שגיאה. {result.get("message","לא ידועה")}'
        )

    except Exception as e:
        print("Exception:", str(e))
        return ym_say_and_hangup(
            "t-התרחשה שגיאה בתקשורת עם שרת ימות המשיח"
        )


def ym_read(var_name, text):
    res = make_response(
        f"read={text}={var_name},4,12,1,Digits"
    )
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


def ym_say_and_hangup(text):
    res = make_response(
        f"id_list_message={text}"
    )
    res.headers["Content-Type"] = "text/plain; charset=utf-8"
    return res


__all__ = ["app"]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
