import os
from .helpers import get_root_path, DictProxy
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

qr_code_dict = DictProxy()

# Jinja2Templates class resolves relative paths to current working directory,
# which is not pymemri/webserver, but path to the plugin that uses it.
# Flask is clever enough to be aware that application may be a part of
# module or package, and changes relative paths to absolute, the first parameter
# of Flask app helps with that:
# app = flask.Flask(__name__, template_folder='template')
# Read the Flask code for better understanding.
# In order to have the same behavior for FastApi get_root_path function is used.
# that is actually copy pasted from Flask.
templates = Jinja2Templates(directory=os.path.join(get_root_path(__name__), "template"))

router = APIRouter()

QR_CODE_KEY = "qr_code"
AUTHENTICATED = "authenticated"


@router.get("/qr", response_class=HTMLResponse)
def qr(request: Request):
    """Returns rendered HTML with QR image"""
    global qr_code_dict
    qr_code_data = qr_code_dict.get(QR_CODE_KEY, None)
    done = qr_code_dict.get(AUTHENTICATED, False)


    the_path = os.path.join(get_root_path(__name__), "template")

    if done:
        return templates.TemplateResponse("success.html", {"request": request})
    else:
        return templates.TemplateResponse("images.html", {"request": request, "chart_output": qr_code_data})
