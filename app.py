# app.py
import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"

@app.route('/create-menu', methods=['GET','POST'])
def create_menu():
    system = request.values.get("system")
    password = request.values.get("password")
    extension = request.values.get("extension")

    if not system:
        return ym_read("system","t-אנא הקישו את מספר המערכת ובסיומה סולמית")
    if not password:
        return ym_read("password","t-אנא הקישו את סיסמת המערכת ובסיומה סולמית")
    if not extension:
        return ym_read("extension","t-אנא הקישו את מספר השלוחה ובסיומה סולמית")

    token=f"{system.strip()}:{password.strip()}"
    clean=extension.strip().replace("*","/").replace("-","/").strip("/")
    path=f"ivr2:/{clean}/ext.ini"

    ext_ini="""type=menu
title=נבנה באמצעות פון קול"""

    url=(f"{YEMOT_API_URL}UploadTextFile"
         f"?token={token}"
         f"&what={path}"
         f"&contents={requests.utils.quote(ext_ini)}")
    try:
        r=requests.post(url,timeout=30)
        print(r.status_code,r.text)
        if r.status_code==200:
            return ym_say("t-השלוחה הוגדרה בהצלחה")
        return ym_say("t-אירעה שגיאה ביצירת השלוחה")
    except Exception as e:
        print(e)
        return ym_say("t-שגיאת תקשורת")

def ym_read(var_name,text):
    res=make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers["Content-Type"]="text/plain; charset=utf-8"
    return res

def ym_say(text):
    res=make_response(f"id_list_message={text}")
    res.headers["Content-Type"]="text/plain; charset=utf-8"
    return res

__all__=["app"]
