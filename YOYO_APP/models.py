from django.db import models

class UserData(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50,unique=True)
    password = models.CharField(max_length=50)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    
    def __str__(self):
        return self.name
    
    def get_email_field_name(self):
        return "email"
    
class Gem(models.Model):
    user = models.ForeignKey("UserData", on_delete=models.CASCADE, related_name="gems")
    name = models.CharField(max_length=100)
    instructions = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Chat(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name="chats")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    gem = models.ForeignKey(Gem, on_delete=models.CASCADE, related_name="chats", null=True, blank=True)


    def __str__(self):
        return f"{self.title} ({self.user.name})"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("bot", "Bot")])
    text = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.text[:20]}"

class SavedInfo(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE, related_name="saved_infos")
    info_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name}: {self.info_text[:50]}..."