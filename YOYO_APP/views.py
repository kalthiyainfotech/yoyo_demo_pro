from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .forms import RegisterForm
from .models import UserData,Message,Chat,Gem
from django.contrib.auth.hashers import check_password
import os ,json
from bardapi import Bard
from django.http import JsonResponse



def register_yoyo(request):
    if request.session.get("user_id"):
        return redirect("home")

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
    if request.session.get("user_id"):
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = UserData.objects.get(email=email)
            if check_password(password, user.password):
                request.session["user_id"] = user.id
                request.session["user_name"] = user.name
                messages.success(request, f"Welcome back, {user.name}!")
                return redirect("home")
            else:
                messages.error(request, "Incorrect password.")
        except UserData.DoesNotExist:
            messages.error(request, "Email not registered.")

    return render(request, "Login.html")


def logout_yoyo(request):
    request.session.flush()  
    return redirect("login")  



os.environ['_BARD_API_KEY'] = "g.a000zQjK6BR93_A9F8DfZ8yOT_5TyCG7mUNu8llCI-Nri1ZBTk7oZhBWihQBRny7k_5UM5Mg5gACgYKAcgSARUSFQHGX2MiMhnVGsHablU-CEYjkqihcxoVAUF8yKrDSgDa2XQHqa44IS6rT7C-0076"


def home_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")

    return render(request, "Yoyo.html", {
        "user": user,
        "chats": chats,
    })


def new_chat(request):
    """Open a blank chat window but do not save to DB yet"""
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")

    return render(request, "Yoyo.html", {
        "user": user,
        "chats": chats,
        "current_chat": None,
        "messages": [],
        "is_new_chat": True,
    })


def chat_detail(request, chat_id=None):
    """Handles chat messages (existing or new)"""
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chat = None
    if chat_id:
        chat = get_object_or_404(Chat, id=chat_id, user=user)

    if request.method == "POST":
        text = request.POST.get("message")
        if text:
            if not chat:
                chat = Chat.objects.create(user=user, title="New Chat")
            if chat.title == "New Chat":
                snippet = " ".join(text.strip().split()[:6])
                chat.title = snippet.capitalize()
                chat.save()
            Message.objects.create(chat=chat, sender="user", text=text)
            try:
                bard = Bard()
                ai_response = bard.get_answer(text).get("content", "⚠️ No reply from Bard.")
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
    })

def send_message(request, chat_id=None):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    user = get_object_or_404(UserData, id=request.session["user_id"])
    data = json.loads(request.body)
    text = data.get("message", "").strip()

    if not text:
        return JsonResponse({"error": "Empty message"}, status=400)

    chat = None
    if chat_id and chat_id != 0:
        chat = get_object_or_404(Chat, id=chat_id, user=user)
    if not chat:
        chat = Chat.objects.create(user=user, title="New Chat")
    if chat.title == "New Chat":
        snippet = " ".join(text.split()[:6])
        chat.title = snippet.capitalize()
        chat.save()
    Message.objects.create(chat=chat, sender="user", text=text)
    try:
        bard = Bard(token=os.environ.get("_BARD_API_KEY"))
        ai_response = bard.get_answer(text).get("content", " No reply from Bard.")
    except Exception as e:
        ai_response = f" Error: {str(e)}"
    Message.objects.create(chat=chat, sender="bot", text=ai_response)

    return JsonResponse({
        "chat_id": chat.id,
        "user_message": text,
        "bot_reply": ai_response,
        "chat_title": chat.title,
    })

def brain_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")

    return render(request, "Brainstormer.html", {
        "user": user,
        "chats": chats,
    })

def Career_guide_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Career_guide.html",{
        "user": user,
        "chats": chats,
    })

def Chess_champ_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Chess_champ.html",{
        "user": user,
        "chats": chats,
    })

def Coding_partner_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Coding_partner.html",{
        "user": user,
        "chats": chats,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "chats": chats,
    })

def ForgotPassword_yoyo(request):
    return render(request,"ForgotPassword.html")

def Learning_coach_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Learning_coach.html",{
        "user": user,
        "chats": chats,
    })

def NewGem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")

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
                return redirect("home")  # redirect to explore gems page
            except Exception as e:
                # Log the error for debugging
                print(f"Error creating Gem: {e}")
                # You could also add error messages to the template context
        else:
            # Log missing data for debugging
            print(f"Missing data - name: {name}, instructions: {instructions}")

    return render(request, "NewGem.html", {
        "user": user,
        "chats": chats,
    })

def Public_Links_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Public_Links.html",{
        "user": user,
        "chats": chats,
    })

def SavedInfo_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"SavedInfo.html",{
        "user": user,
        "chats": chats,
    })

def Search_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Search.html",{
        "user": user,
        "chats": chats,
    })

def Upgrad_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Upgrad.html",{
        "user": user,
        "chats": chats,
    })

def Writing_editor_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Writing_editor.html",{
        "user": user,
        "chats": chats,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    chats = Chat.objects.filter(user=user).order_by("-created_at")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "chats": chats,
    })