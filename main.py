from fastapi import FastAPI, Request, Form, Depends, status, UploadFile, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from auth import authenticate_user
from db import File, User, SessionLocal  # No get_db here; we define it below
from storage import download_file_obj, upload_file_obj
import os

# --- App Setup ---
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="a-strong-secret")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Get logged in user from session ---
def get_logged_in_user(request: Request, db=Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return None
    user = db.query(User).filter_by(username=username).first()
    return user

# --- Home Page ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    files = db.query(File).filter_by(user_id=user.id).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "files": files})

# --- Login Page ---
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    request.session["user"] = username
    return RedirectResponse("/", status_code=303)

# --- Logout ---
@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

# --- Upload File ---
@app.post("/upload/", response_class=HTMLResponse)
def web_upload(request: Request, file: UploadFile = UploadFile(...), db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    try:
        storage_path = f"{user.id}/{file.filename}-{os.urandom(8).hex()}"
        upload_file_obj(file.file, storage_path)
        meta = File(
            filename=file.filename,
            user_id=user.id,
            storage_path=storage_path,
            size=file.size or 0
        )
        db.add(meta)
        db.commit()
    except Exception as e:
        files = db.query(File).filter_by(user_id=user.id).all()
        return templates.TemplateResponse("index.html", {
            "request": request, "user": user, "files": files,
            "upload_error": f"Upload failed: {e}"
        })

    return RedirectResponse("/", status_code=303)

# --- Download File ---
@app.get("/download/{file_id}")
def web_download(file_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    meta = db.query(File).filter_by(id=file_id).first()
    if not meta or meta.user_id != user.id:
        return RedirectResponse("/", status_code=303)
    content = download_file_obj(meta.storage_path)
    return Response(content, media_type="application/octet-stream", headers={
        "Content-Disposition": f"attachment; filename={meta.filename}"
    })
