from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .forms import RegisterForm
from .models import UserData,Message,Chat,Gem,SavedInfo
from django.contrib.auth.hashers import check_password
import os ,json
from bardapi import Bard
from django.http import JsonResponse
from django.db import transaction
from datetime import date, timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core import signing

os.environ['_BARD_API_KEY'] = "g.a000zQjK6BR93_A9F8DfZ8yOT_5TyCG7mUNu8llCI-Nri1ZBTk7oZhBWihQBRny7k_5UM5Mg5gACgYKAcgSARUSFQHGX2MiMhnVGsHablU-CEYjkqihcxoVAUF8yKrDSgDa2XQHqa44IS6rT7C-0076"



def _encode_id(kind, numeric_id):
    """Return an opaque, signed token for a numeric id using SECRET_KEY.

    kind: a short string namespace (e.g., "user", "chat", "gem", "savedinfo").
    """
    return signing.dumps({"id": int(numeric_id)}, salt=f"yoyo:{kind}")


def _resolve_id(kind, value):
    """Resolve either a signed token or a plain integer string to an int id.

    Accepts legacy integer ids (e.g., "123") for backward compatibility.
    """
    if value is None:
        return None
    # If already an int, return
    if isinstance(value, int):
        return int(value)
    # Value could be "123" or a signed token
    text = str(value)
    # Quick path: plain integer
    try:
        return int(text)
    except (TypeError, ValueError):
        pass
    # Try signed token
    try:
        data = signing.loads(text, salt=f"yoyo:{kind}")
        return int(data.get("id"))
    except Exception:
        # As a last resort, raise 404 by returning None; callers should handle
        return None


def _get_session_accounts(request):
    """Return list of account dicts in session (may be empty)."""
    return request.session.get("accounts", [])

def _save_session_accounts(request, accounts):
    request.session["accounts"] = accounts
    request.session.modified = True

def _ensure_active_account(request):
    """Ensure active_account_id exists and points to a valid entry in accounts."""
    active_id = request.session.get("active_account_id")
    accounts = _get_session_accounts(request)
    if active_id and any(int(a["id"]) == int(active_id) for a in accounts):
        return
    if accounts:
        request.session["active_account_id"] = accounts[0]["id"]
        request.session.modified = True

def _append_account_to_session(request, user):
    accounts = _get_session_accounts(request)
    if not any(int(a["id"]) == int(user.id) for a in accounts):
        accounts.append({"id": int(user.id), "name": user.name, "email": user.email})
        _save_session_accounts(request, accounts)
    # make this user the active one
    request.session["active_account_id"] = int(user.id)
    request.session.modified = True

def _replace_with_account(request, user):
    accounts = [{"id": int(user.id), "name": user.name, "email": user.email}]
    _save_session_accounts(request, accounts)
    request.session["active_account_id"] = int(user.id)
    request.session.modified = True

def _get_active_user(request):
    _ensure_active_account(request)
    active_id = request.session.get("active_account_id")
    if not active_id:
        return None
    try:
        return UserData.objects.get(id=active_id)
    except UserData.DoesNotExist:
        # remove invalid account id from session and retry
        accounts = [a for a in _get_session_accounts(request) if int(a["id"]) != int(active_id)]
        _save_session_accounts(request, accounts)
        request.session.pop("active_account_id", None)
        request.session.modified = True
        return _get_active_user(request)

# ---------- Views ----------
def register_yoyo(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, "Register.html", {"form": form})

def login_yoyo(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = UserData.objects.get(email=email)
            if check_password(password, user.password):
                accounts = request.session.get("accounts", [])

                # avoid duplicates
                if user.id not in [acc["id"] for acc in accounts]:
                    accounts.append({"id": user.id, "name": user.name, "email": user.email})

                request.session["accounts"] = accounts
                request.session["user_id"] = user.id
                request.session["user_name"] = user.name
                # set active account for consistency with switch behavior
                request.session["active_account_id"] = int(user.id)

                messages.success(request, f"Welcome back, {user.name}!")
                return redirect("home")
            else:
                messages.error(request, "Incorrect password.")
        except UserData.DoesNotExist:
            messages.error(request, "Email not registered.")

    return render(request, "Login.html")

def switch_account(request, account_id):
    """Switch active_account_id to one of the accounts already in the session (GET link is fine)."""
    accounts = _get_session_accounts(request)
    resolved_id = _resolve_id("user", account_id)
    if resolved_id is not None and any(int(a["id"]) == int(resolved_id) for a in accounts):
        # update active account id
        request.session["active_account_id"] = int(resolved_id)
        # also update the session's current user fields so templates/views reflect the switch
        try:
            user = UserData.objects.get(id=resolved_id)
            request.session["user_id"] = int(user.id)
            request.session["user_name"] = user.name
        except UserData.DoesNotExist:
            pass
        request.session.modified = True
        messages.success(request, "Switched account.")
        next_url = request.GET.get("next") or reverse("home")
        return redirect(next_url)
    return HttpResponseForbidden("You cannot switch to that account.")

def logout_yoyo(request):
    # Clear the whole session
    request.session.flush()
    
    # Optional: add a message
    messages.success(request, "Signed out.")
    
    # Redirect to login page
    return redirect("login") 

@require_POST
def upload_profile_image(request):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "Unauthorized"}, status=401)
    user = get_object_or_404(UserData, id=request.session["user_id"])
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"success": False, "message": "No image provided"}, status=400)
    user.profile_image = image
    user.save()
    return JsonResponse({"success": True, "image_url": user.profile_image.url})

def home_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")
    

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]


    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

  
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "YOYO.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def new_chat(request):
    """Open a blank chat window, linked to a gem if provided"""
    if not request.session.get("user_id"):
        return redirect("login")
    

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

   
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    gem_id = request.GET.get("gem_id")
    gem = None
    if gem_id:
        resolved_gem_id = _resolve_id("gem", gem_id)
        gem = get_object_or_404(Gem, id=resolved_gem_id, user=user)

    
    if gem:
        chat = Chat.objects.create(
            user=user,
            title=f"Chat about {gem.name}",
            gem=gem
        )
        return redirect("chat_detail", chat_id=chat.id)

    
    return render(request, "Yoyo.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "current_chat": None,
        "messages": [],
        "is_new_chat": True,
        "other_accounts": other_accounts,
    })

def chat_detail(request, chat_id=None):
    """Handles chat messages (existing or new)"""
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    # Recent = chats without gem
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    # Story Book = gems with their chats
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    chat = None
    if chat_id:
        resolved_chat_id = _resolve_id("chat", chat_id)
        chat = get_object_or_404(Chat, id=resolved_chat_id, user=user)

    if request.method == "POST":
        text = request.POST.get("message", "").strip()
        image = request.FILES.get("image")
        if text or image:
            if not chat:
                chat = Chat.objects.create(user=user, title="New Chat")
            if chat.title == "New Chat":
                snippet_source = text or "Image message"
                snippet = " ".join(snippet_source.strip().split()[:6])
                chat.title = snippet.capitalize()
                chat.save()
            Message.objects.create(chat=chat, sender="user", text=text, image=image)
            try:
                bard = Bard()
                prompt = text or "Describe the attached image."
                ai_response = bard.get_answer(prompt).get("content", "⚠️ No reply from Bard.")
            except Exception as e:
                ai_response = f" Error: {str(e)}"
            Message.objects.create(chat=chat, sender="bot", text=ai_response)

            return redirect("chat_detail", chat_id=chat.id)
    return render(request, "Yoyo.html", {
        "user": user,
        "chats": Chat.objects.filter(user=user).order_by("-created_at"),
        "current_chat": chat,
        "messages": chat.messages.all() if chat else [],
        "is_new_chat": chat is None,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def send_message(request, chat_id=None):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = get_object_or_404(UserData, id=request.session["user_id"])
    text = ""
    image = None
    # Support JSON and multipart/form-data
    content_type = request.META.get("CONTENT_TYPE", "")
    if content_type.startswith("multipart/form-data"):
        text = request.POST.get("message", "").strip()
        image = request.FILES.get("image")
    else:
        try:
            data = json.loads(request.body or b"{}")
        except Exception:
            data = {}
        text = str(data.get("message", "")).strip()

    if not text and not image:
        return JsonResponse({"error": "Empty message"}, status=400)

    chat = None
    if chat_id and str(chat_id) != "0":
        resolved_chat_id = _resolve_id("chat", chat_id)
        chat = get_object_or_404(Chat, id=resolved_chat_id, user=user)
    if not chat:
        chat = Chat.objects.create(user=user, title="New Chat")
    if chat.title == "New Chat":
        snippet_source = text or "Image message"
        snippet = " ".join(snippet_source.split()[:6])
        chat.title = snippet.capitalize()
        chat.save()
    Message.objects.create(chat=chat, sender="user", text=text, image=image)
    try:
        bard = Bard(token=os.environ.get("_BARD_API_KEY"))
        prompt = text or "Describe the attached image."
        ai_response = bard.get_answer(prompt).get("content", " No reply from Bard.")
    except Exception as e:
        ai_response = f" Error: {str(e)}"
    Message.objects.create(chat=chat, sender="bot", text=ai_response)

    return JsonResponse({
        "chat_id": chat.id,
        "chat_token": _encode_id("chat", chat.id),
        "user_message": text,
        "bot_reply": ai_response,
        "chat_title": chat.title,
    })

def brain_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "Brainstormer.html", {
        "user": user,
        "other_accounts": other_accounts,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Career_guide_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Career_guide.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def Chess_champ_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Chess_champ.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def Coding_partner_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Coding_partner.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })


token_generator = PasswordResetTokenGenerator()
def ForgotPassword_yoyo(request):
    return render(request,"ForgotPassword.html")

def ForgotPassword_yoyo(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = UserData.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = token_generator.make_token(user)

            reset_link = request.build_absolute_uri(
                f"/reset-password/{uid}/{token}/"
            )

            # Send reset email
            send_mail(
                subject="Password Reset Request – YOYO",
                message=f"Hi {user.name},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, you can ignore this email.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )

            messages.success(request, "Password reset link sent to your email.")
            return redirect("login")
        except UserData.DoesNotExist:
            messages.error(request, "Email not found.")
    
    return render(request, "ForgotPassword.html")

# Step 2: Reset Password
def ResetPassword_yoyo(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = UserData.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, UserData.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
            else:
                user.password = make_password(password)
                user.save()
                messages.success(request, "Password reset successful! Please login.")
                return redirect("login")
        return render(request, "ResetPassword.html", {"validlink": True})
    else:
        messages.error(request, "Invalid or expired link.")
        return render(request, "ResetPassword.html", {"validlink": False})

def Learning_coach_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Learning_coach.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def NewGem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    
    

    if request.method == "POST":
        name = request.POST.get("name")
        instructions = request.POST.get("instructions")

        if name and instructions:
            try:
                Gem.objects.create(
                    user=user,
                    name=name,
                    instructions=instructions,
                )
                return redirect("home") 
            except Exception as e:
               
                print(f"Error creating Gem: {e}")
               
        else:
           
            print(f"Missing data - name: {name}, instructions: {instructions}")

    return render(request, "NewGem.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def gem_detail(request, gem_id):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    resolved_gem_id = _resolve_id("gem", gem_id)
    gem = get_object_or_404(Gem, id=resolved_gem_id, user=user)

    return render(request, "NewGem.html", {"gem": gem, "user": user})

def Public_Links_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]    

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "Public_Links.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def SavedInfo_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    
    # Get saved info for the user
    saved_infos = SavedInfo.objects.filter(user=user).order_by("-created_at")
    
    # Convert to JSON for JavaScript
    saved_infos_json = json.dumps([
        {
            'id': info.id,
            'info_text': info.info_text,
            'created_at': info.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for info in saved_infos
    ])
    
    return render(request,"SavedInfo.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "saved_infos": saved_infos_json,
        "other_accounts": other_accounts,
    })

def save_info(request):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "User not authenticated"})
    
    
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            info_text = data.get("info_text", "").strip()
            
            if not info_text:
                return JsonResponse({"success": False, "message": "Info text cannot be empty"})
            
            user = get_object_or_404(UserData, id=request.session["user_id"])
            
            # Create new saved info
            saved_info = SavedInfo.objects.create(
                user=user,
                info_text=info_text
            )
            
            return JsonResponse({
                "success": True, 
                "message": "Info saved successfully",
                "saved_info": {
                    "id": saved_info.id,
                    "info_text": saved_info.info_text,
                    "created_at": saved_info.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error saving info: {str(e)}"})
    
    return JsonResponse({"success": False, "message": "Invalid request method"})

def delete_saved_info(request, info_id):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "User not authenticated"})
    
    if request.method == "DELETE":
        try:
            user = get_object_or_404(UserData, id=request.session["user_id"])
            resolved_info_id = _resolve_id("savedinfo", info_id)
            saved_info = get_object_or_404(SavedInfo, id=resolved_info_id, user=user)
            saved_info.delete()
            
            return JsonResponse({"success": True, "message": "Info deleted successfully"})
            
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error deleting info: {str(e)}"})
    
    return JsonResponse({"success": False, "message": "Invalid request method"})

def delete_all_saved_info(request):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "User not authenticated"})
    
    if request.method == "DELETE":
        try:
            user = get_object_or_404(UserData, id=request.session["user_id"])
            SavedInfo.objects.filter(user=user).delete()
            
            return JsonResponse({"success": True, "message": "All info deleted successfully"})
            
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error deleting all info: {str(e)}"})
    
    return JsonResponse({"success": False, "message": "Invalid request method"})

def update_saved_info(request, info_id):
    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "message": "User not authenticated"})
    
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            info_text = data.get("info_text", "").strip()
            
            if not info_text:
                return JsonResponse({"success": False, "message": "Info text cannot be empty"})
            
            user = get_object_or_404(UserData, id=request.session["user_id"])
            resolved_info_id = _resolve_id("savedinfo", info_id)
            saved_info = get_object_or_404(SavedInfo, id=resolved_info_id, user=user)
            
            saved_info.info_text = info_text
            saved_info.save()
            
            return JsonResponse({
                "success": True, 
                "message": "Info updated successfully",
                "saved_info": {
                    "id": saved_info.id,
                    "info_text": saved_info.info_text,
                    "created_at": saved_info.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error updating info: {str(e)}"})
    
    return JsonResponse({"success": False, "message": "Invalid request method"})

def Search_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")
    

    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
   
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    return render(request,"Search.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "today": today,
        "yesterday": yesterday,
        "other_accounts": other_accounts,
    })

def Upgrad_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Upgrad.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def Writing_editor_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Writing_editor.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
        "other_accounts": other_accounts,
    })
    
def copy_gem(request, gem_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    if not request.session.get("user_id"):
        return JsonResponse({"success": False, "error": "Not logged in"})

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]
    resolved_gem_id = _resolve_id("gem", gem_id)
    gem = get_object_or_404(Gem, id=resolved_gem_id, user=user)

    try:
        with transaction.atomic():
            
            new_gem = Gem.objects.create(
                user=user,
                name=f"{gem.name} (Copy)",
                
            )

         
            for chat in gem.chats.all():   
                new_chat = Chat.objects.create(
                    user=user,
                    gem=new_gem,
                    title=chat.title,
                 
                )

              
                for msg in chat.messages.all():  
                    Message.objects.create(
                        chat=new_chat,
                        sender=msg.sender,
                        content=msg.content,
                        
                    )

        return JsonResponse({"success": True, "new_gem_id": new_gem.id, "new_gem_token": _encode_id("gem", new_gem.id), "new_gem_name": new_gem.name, "other_accounts": other_accounts})

    except Exception as e:
        print("COPY ERROR:", e)
        return JsonResponse({"success": False, "error": str(e)})
    
def rename_chat(request, chat_id):
    if request.method == "POST":
        resolved_chat_id = _resolve_id("chat", chat_id)
        chat = get_object_or_404(Chat, id=resolved_chat_id, user_id=request.session["user_id"])
        data = json.loads(request.body)
        chat.title = data.get("title", chat.title)
        chat.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

def delete_chat(request, chat_id):
    if request.method == "POST":
        resolved_chat_id = _resolve_id("chat", chat_id)
        chat = get_object_or_404(Chat, id=resolved_chat_id, user_id=request.session["user_id"])
        chat.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

def newgem_preview_chat(request):
    """Handle preview chat for NewGem with Bard API integration"""
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = get_object_or_404(UserData, id=request.session["user_id"])
    accounts = request.session.get("accounts", [])

    # exclude current
    other_accounts = [acc for acc in accounts if acc["id"] != user.id]
    data = json.loads(request.body)
    

    message = data.get("message", "").strip()
    gem_instructions = data.get("instructions", "").strip()
    gem_name = data.get("name", "New Gem").strip()

    if not message:
        return JsonResponse({"error": "Empty message"}, status=400)

    try:
        
        if gem_instructions:
            
            custom_prompt = f"You are a specialized AI assistant with the following characteristics and instructions:\n\n{gem_instructions}\n\nNow, please respond to this user query: {message}"
        else:
            custom_prompt = message

       
        bard = Bard(token=os.environ.get("_BARD_API_KEY"))
        ai_response = bard.get_answer(custom_prompt).get("content", "⚠️ No reply from Bard.")
        
        return JsonResponse({
            "user_message": message,
            "bot_reply": ai_response,
            "gem_name": gem_name,
            "other_accounts": other_accounts,
            "success": True
        })
        
    except Exception as e:
        return JsonResponse({
            "error": f"Error getting AI response: {str(e)}",
            "success": False
        }, status=500)
        
def rename_gem(request, gem_id):
    """Rename a gem in Story Book"""
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user = get_object_or_404(UserData, id=request.session["user_id"])
    resolved_gem_id = _resolve_id("gem", gem_id)
    gem = get_object_or_404(Gem, id=resolved_gem_id, user=user)

    if request.method == "POST":
        data = json.loads(request.body)
        new_name = data.get("name", "").strip()
        if new_name:
            gem.name = new_name
            gem.save()
            return JsonResponse({"success": True, "new_name": gem.name})
        return JsonResponse({"error": "Invalid name"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

def delete_gem(request, gem_id):
    """Delete a gem from Story Book"""
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user = get_object_or_404(UserData, id=request.session["user_id"])
    resolved_gem_id = _resolve_id("gem", gem_id)
    gem = get_object_or_404(Gem, id=resolved_gem_id, user=user)

    if request.method == "POST":
        gem.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)

def chat_page(request, gem_id):
    resolved_gem_id = _resolve_id("gem", gem_id)
    gem = get_object_or_404(Gem, id=resolved_gem_id, user=request.session.get("user_id"))
    chats = gem.chats.all().order_by("-created_at")

    return render(request, "chat_page.html", {
        "gem": gem,
        "chats": chats,
    })

def Chat_out(request):
    return render(request, "Chat.html")

@csrf_exempt
@require_POST
def chat_out_send(request):
    """Public chat endpoint: no auth, no DB writes. Sends prompt to Bard and returns reply.

    Accepts either JSON {"message": "..."} or form-data with field "message".
    """
    # Parse input
    content_type = request.META.get("CONTENT_TYPE", "")
    if content_type.startswith("multipart/form-data"):
        text = (request.POST.get("message", "") or "").strip()
    else:
        try:
            data = json.loads(request.body or b"{}")
        except Exception:
            data = {}
        text = str(data.get("message", "")).strip()

    if not text:
        return JsonResponse({"error": "Empty message"}, status=400)

    # Call Bard without persisting anything
    try:
        bard = Bard(token=os.environ.get("_BARD_API_KEY"))
        ai_response = bard.get_answer(text).get("content", " No reply from Bard.")
    except Exception as e:
        return JsonResponse({"error": f"Error getting AI response: {str(e)}"}, status=500)

    return JsonResponse({
        "user_message": text,
        "bot_reply": ai_response,
        "success": True,
    })