# forms.py
from django import forms
from .models import UserData

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    c_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = UserData
        fields = ["name", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        c_password = cleaned_data.get("c_password")
        if password != c_password:
            raise forms.ValidationError("Passwords do not match.")
