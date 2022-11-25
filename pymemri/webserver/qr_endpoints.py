import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .helpers import DictProxy, get_root_path

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
QR_STRING_KEY = "qr_string"
AUTHENTICATED = "authenticated"
REQUIRES2FACTOR = "requires2factor"


@router.get("/qr", response_class=HTMLResponse)
def qr(request: Request):
    """Returns rendered HTML with QR image"""
    global qr_code_dict
    qr_code_data = qr_code_dict.get(QR_CODE_KEY, None)
    done = qr_code_dict.get(AUTHENTICATED, False)
    requires2factor = (qr_code_dict.get(REQUIRES2FACTOR, False),)

    the_path = os.path.join(get_root_path(__name__), "template")

    # TODO - add a template for 2FA
    if done:
        return templates.TemplateResponse("success.html", {"request": request})
    else:
        return templates.TemplateResponse(
            "images.html", {"request": request, "chart_output": qr_code_data}
        )


@router.get("/qr_svg", response_class=JSONResponse)
def qr_svg():
    """Returns the QR svg as json"""
    global qr_code_dict

    content = {
        "qr": qr_code_dict.get(QR_CODE_KEY, None),
        "authenticated": qr_code_dict.get(AUTHENTICATED, False),
        "requires2factor": qr_code_dict.get(REQUIRES2FACTOR, False),
    }

    return JSONResponse(content=content, headers={"Access-Control-Allow-Origin": "*"})


@router.get("/qr_string", response_class=JSONResponse)
def qr_string():
    """Returns the QR svg as json"""
    global qr_code_dict

    content = {
        "qr": qr_code_dict.get(QR_STRING_KEY, None).decode("utf-8"),
        "authenticated": qr_code_dict.get(AUTHENTICATED, False),
        "requires2factor": qr_code_dict.get(REQUIRES2FACTOR, False),
    }

    return JSONResponse(content=content, headers={"Access-Control-Allow-Origin": "*"})
