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


    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

  
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "YOYO.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def new_chat(request):
    """Open a blank chat window, linked to a gem if provided"""
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

   
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    gem_id = request.GET.get("gem_id")
    gem = None
    if gem_id:
        gem = get_object_or_404(Gem, id=gem_id, user=user)

    
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
    })

def chat_detail(request, chat_id=None):
    """Handles chat messages (existing or new)"""
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    # Recent = chats without gem
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    # Story Book = gems with their chats
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
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
        "recent_chats": recent_chats,
        "story_gems": story_gems,
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

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "Brainstormer.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Career_guide_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Career_guide.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Chess_champ_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Chess_champ.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Coding_partner_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Coding_partner.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def ForgotPassword_yoyo(request):
    return render(request,"ForgotPassword.html")

def Learning_coach_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Learning_coach.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def NewGem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
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
    })

def gem_detail(request, gem_id):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])
    gem = get_object_or_404(Gem, id=gem_id, user=user)

    return render(request, "NewGem.html", {"gem": gem, "user": user})

def Public_Links_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")

    return render(request, "Public_Links.html", {
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def SavedInfo_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"SavedInfo.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Search_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Search.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Upgrad_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Upgrad.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Writing_editor_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Writing_editor.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })

def Explore_Gem_yoyo(request):
    if not request.session.get("user_id"):
        return redirect("login")

    user = get_object_or_404(UserData, id=request.session["user_id"])

    
    recent_chats = Chat.objects.filter(user=user, gem__isnull=True).order_by("-created_at")

    
    story_gems = Gem.objects.filter(user=user).prefetch_related("chats")
    return render(request,"Explore_Gem.html",{
        "user": user,
        "recent_chats": recent_chats,
        "story_gems": story_gems,
    })
    
def rename_chat(request, chat_id):
    if request.method == "POST":
        chat = get_object_or_404(Chat, id=chat_id, user_id=request.session["user_id"])
        data = json.loads(request.body)
        chat.title = data.get("title", chat.title)
        chat.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

def delete_chat(request, chat_id):
    if request.method == "POST":
        chat = get_object_or_404(Chat, id=chat_id, user_id=request.session["user_id"])
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
    gem = get_object_or_404(Gem, id=gem_id, user=user)

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
    gem = get_object_or_404(Gem, id=gem_id, user=user)

    if request.method == "POST":
        gem.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)