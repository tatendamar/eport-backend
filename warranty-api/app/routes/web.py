"""
Web interface routes for the Warranty Register app.
Provides a simple HTML interface for viewing registered warranties.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import math

from ..database import get_db
from .. import models
from ..auth import verify_password, create_access_token
from pathlib import Path

# Use package-relative templates directory
templates_dir = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(templates_dir))
from ..auth import validate_api_key_value

router = APIRouter(prefix="/web", tags=["web"])

# Simple session storage (in production, use Redis or database)
sessions = {}


def get_session_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    """Get user from session cookie."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    
    user_email = sessions[session_id]
    user = db.query(models.User).filter(models.User.email == user_email).first()
    return user


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Render login page."""
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle login form submission."""
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"}, status_code=401)
    
    if user.is_active != 'Y':
        return templates.TemplateResponse("login.html", {"request": request, "error": "Account is inactive"}, status_code=403)
    
    # Create session
    import secrets
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = user.email
    
    response = RedirectResponse(url="/web/dashboard", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=3600  # 1 hour
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    """Handle logout."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/web/login", status_code=303)
    response.delete_cookie("session_id")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Render dashboard with warranty list."""
    user = get_session_user(request, db)
    
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    # Get warranties with pagination
    page_size = 20
    query = db.query(models.Warranty)
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    
    warranties = query.order_by(
        models.Warranty.registered_at.desc()
    ).offset(offset).limit(page_size).all()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "warranties": warranties,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@router.get("/", response_class=HTMLResponse)
async def web_root(request: Request, db: Session = Depends(get_db)):
    """Redirect to dashboard or login."""
    user = get_session_user(request, db)
    if user:
        return RedirectResponse(url="/web/dashboard", status_code=303)
    return RedirectResponse(url="/web/login", status_code=303)


@router.get("/warranty/{warranty_id}", response_class=HTMLResponse)
async def warranty_detail(
    request: Request,
    warranty_id: str,
    db: Session = Depends(get_db)
):
    """View warranty details by warranty ID."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    warranty = db.query(models.Warranty).filter(
        models.Warranty.id == warranty_id
    ).first()
    
    if not warranty:
        return RedirectResponse(url="/web/dashboard", status_code=303)
    
    return templates.TemplateResponse("warranty_detail.html", {"request": request, "user": user, "warranty": warranty})


@router.get("/warranty/{warranty_id}/status", response_class=HTMLResponse)
async def warranty_status_page(
    request: Request,
    warranty_id: str,
    db: Session = Depends(get_db)
):
    """Show update status form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    warranty = db.query(models.Warranty).filter(
        models.Warranty.id == warranty_id
    ).first()
    
    if not warranty:
        return RedirectResponse(url="/web/dashboard", status_code=303)
    
    return templates.TemplateResponse("warranty_status.html", {"request": request, "user": user, "warranty": warranty, "message": None, "success": False})


@router.post("/warranty/{warranty_id}/status", response_class=HTMLResponse)
async def warranty_status_update(
    request: Request,
    warranty_id: str,
    new_status: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update warranty status."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    warranty = db.query(models.Warranty).filter(
        models.Warranty.id == warranty_id
    ).first()
    
    if not warranty:
        return RedirectResponse(url="/web/dashboard", status_code=303)
    
    # Validate status
    valid_statuses = ['registered', 'active', 'expired', 'claimed']
    if new_status not in valid_statuses:
        return templates.TemplateResponse(
            "warranty_status.html",
            {"request": request, "user": user, "warranty": warranty, "message": f"Invalid status: {new_status}", "success": False},
        )
    
    # Update status
    warranty.warranty_status = models.WarrantyStatus(new_status)
    db.commit()
    db.refresh(warranty)
    
    return templates.TemplateResponse(
        "warranty_status.html",
        {"request": request, "user": user, "warranty": warranty, "message": f"Status updated to '{new_status}' successfully!", "success": True},
    )


@router.get("/check-asset", response_class=HTMLResponse)
async def check_asset_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Show check asset form."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    return templates.TemplateResponse(
        "check_asset.html",
        {"request": request, "user": user, "warranty": None, "message": None, "error": None, "found": False, "asset_id": None},
    )


@router.post("/check-asset", response_class=HTMLResponse)
async def check_asset_submit(
    request: Request,
    asset_id: str = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """Check warranty by asset ID (requires API key)."""
    user = get_session_user(request, db)
    if not user:
        return RedirectResponse(url="/web/login", status_code=303)
    
    # Validate API key
    if not validate_api_key_value(api_key):
        return templates.TemplateResponse(
            "check_asset.html",
            {"request": request, "user": user, "warranty": None, "message": None, "error": "Invalid API key", "found": False, "asset_id": asset_id},
        )

    # Check for warranty
    warranty = db.query(models.Warranty).filter(models.Warranty.asset_id == asset_id).first()

    if warranty:
        return templates.TemplateResponse(
            "check_asset.html",
            {"request": request, "user": user, "warranty": warranty, "message": "Warranty found for this asset!", "error": None, "found": True, "asset_id": asset_id},
        )

    return templates.TemplateResponse(
        "check_asset.html",
        {"request": request, "user": user, "warranty": None, "message": "No warranty registered for this asset.", "error": None, "found": False, "asset_id": asset_id},
    )
