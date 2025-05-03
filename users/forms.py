# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Role, Permission

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth', 'address', 'contact')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Assign default role (User) if not specified
        if not user.role:
            default_role = Role.objects.filter(name="User").first()
            if default_role:
                user.role = default_role
        
        if commit:
            user.save()
        return user

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