# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Role, Permission

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'address', 'contact', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'address', 'contact', 'role')

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ('name', 'description')

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ('name', 'code', 'description')