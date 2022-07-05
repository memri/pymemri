import multiprocessing
import os

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

qr_code_dict = multiprocessing.Manager().dict()
templates = Jinja2Templates(directory="/home/szym/memri/pymemri/pymemri/webserver/template")

router = APIRouter()


QR_CODE_KEY = "qr_code"
AUTHENTICATED = "authenticated"


@router.get("/qr", response_class=HTMLResponse)
def qr(request: Request):
    global qr_code_dict
    qr_code_data = qr_code_dict.get(QR_CODE_KEY, None)
    done = qr_code_dict.get(AUTHENTICATED, False)

    print(f"DEBUG: done {done} qr code: {qr_code_data}")
    print(f"CWD{os.getcwd()}")
    if done:
        return templates.TemplateResponse("success.html", {"request": request})
    else:
        return templates.TemplateResponse("images.html", {"request": request, "chart_output": qr_code_data})

# # TODO: if globals are meh, then:
# def get_router():
#     router = APIRouter()
#     qr_code_dict = multiprocessing.Manager().dict()

#     def qr():
#         qr_code_data = qr_code_dict.get(QR_CODE_KEY, None)
#         done = qr_code_dict.get(AUTHENTICATED, False)

#         print(f"DEBUG: qr code: {qr_code_data}")

#     router.add_api_route("/qr", qr)

#     return router, qr_code_dict
