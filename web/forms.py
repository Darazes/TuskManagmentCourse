from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import PasswordInput, ModelForm
from django.core.validators import validate_email

from web.models import *


# форма авторизации

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)

class MySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password2'].label = 'Подтвердите пароль'

class LoginForm(forms.Form):
    username = forms.CharField(required=True, label='Username')
    password = forms.CharField(required=True, label='Пароль')

class RegisterForm(ModelForm):
    username = forms.CharField(
        min_length=3, max_length=10, required=True, label='Никнейм',
        validators=[RegexValidator(
            regex='^[a-zA-Z0-9]*$',
            message='Может содержать только латинские буквы и цифры',
            code='invalid_username'
        )]
    )
    email = forms.EmailField(min_length=3, required=True, label='Email')
    password = forms.CharField(widget=PasswordInput(), required=True, label='Пароль')
    password_confirm = forms.CharField(widget=PasswordInput(), required=True, label='Повторите пароль')

    class Meta:
        model = get_user_model()
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError('Введите корректный email')

        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data

def clean(self):
    cleaned_data = super(RegisterForm, self).clean()
    # валидация паролей
    password = cleaned_data.get("password")
    password_confirm = cleaned_data.get("password_confirm")

class StatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'id': 'id_status'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].empty_label = None


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = ['file']

class ContactForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=100)
    email = forms.EmailField(label='Email')
    message = forms.CharField(label='Сообщение', widget=forms.Textarea)