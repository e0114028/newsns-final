from dataclasses import dataclass
import email
import re
from xml.dom import ValidationErr
from django import forms

from core.models import User

class RegisterForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="パスワード認証",widget=forms.PasswordInput)


#パスワード不一致時
    def match_password(self):
        date = self.cleaned_data
        password = data.get("password")
        password2 = data.get("password2")

        if password != password2:
            raise ValidationErr("同じものを入れろ")
        return data


#既登録のエラー
    def double_email(self):
        email = self.cleaned_data.get("email")
        query_set = User.objects.filter(username=username)
        if username == query_set:
            return ValidationErr("それ使われてるよ")

        return username
