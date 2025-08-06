import os
from fastapi import FastAPI, Request, Form, UploadFile, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from db import init_db, SessionLocal, User, File
from storage import upload_file_obj, generate_presigned_url
from auth import create_user, authenticate_user, get_db, get_logged_in_user

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret-session-key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.is_admin or user.role == "admin":
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/user", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def post_login(request: Request, db: Session = Depends(get_db),
               email: str = Form(...), password: str = Form(...)):
    user = authenticate_user(db, email, password)
    if not user:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            return RedirectResponse(f"/register?prefill_email={email}", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    request.session["user_email"] = user.email
    return RedirectResponse("/", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request, prefill_email: str = ""):
    return templates.TemplateResponse("register.html", {"request": request, "prefill_email": prefill_email})

@app.post("/register", response_class=HTMLResponse)
def post_register(request: Request, db: Session = Depends(get_db),
                  username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if db.query(User).filter((User.email == email) | (User.username == username)).first():
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email or username already in use!",
            "prefill_email": email
        })
    user = create_user(db, username=username, email=email, password=password, role="user")
    request.session["user_email"] = user.email
    return RedirectResponse("/", status_code=303)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/user", response_class=HTMLResponse)
def user_panel(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user or user.is_admin or user.role == "admin":
        return RedirectResponse("/login", status_code=303)
    files = db.query(File).filter_by(user_id=user.id).all()
    return templates.TemplateResponse("user_panel.html", {"request": request, "user": user, "files": files})

@app.post("/upload/", response_class=HTMLResponse)
def upload(request: Request, db: Session = Depends(get_db), file: UploadFile = UploadFile(...)):
    user = get_logged_in_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    storage_path = f"{user.id}/{file.filename}-{os.urandom(8).hex()}"

    try:
        file_bytes = file.file.read()
        size = len(file_bytes)

        from io import BytesIO
        upload_file_obj(BytesIO(file_bytes), storage_path)

        meta = File(
            filename=file.filename,
            user_id=user.id,
            storage_path=storage_path,
            size=size
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)

    except Exception as e:
        files = db.query(File).filter_by(user_id=user.id).all()
        return templates.TemplateResponse("user_panel.html", {
            "request": request,
            "user": user,
            "files": files,
            "upload_error": f"Upload failed: {e}"
        })

    return RedirectResponse("/user", status_code=303)

@app.get("/download/{file_id}")
def download_file(file_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    meta = db.query(File).filter_by(id=file_id).first()
    if not meta:
        return HTMLResponse("File does not exist", status_code=404)
    if user is None or (meta.user_id != user.id and not (user.is_admin or user.role == "admin")):
        return HTMLResponse("Unauthorized", status_code=403)

    try:
        url = generate_presigned_url(meta.storage_path)
        return RedirectResponse(url, status_code=303)
    except Exception as e:
        return HTMLResponse(f"Download failed: {e}", status_code=500)

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user or not (user.is_admin or user.role == "admin"):
        return RedirectResponse("/login", status_code=303)
    files = db.query(File).all()
    users = db.query(User).all()
    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "user": user,
        "files": files,
        "users": users
    })
