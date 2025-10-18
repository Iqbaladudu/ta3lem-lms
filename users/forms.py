from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from courses.models import Course
from .models import User


class CourseEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(CourseEnrollForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()


class StudentRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if role != "student":
            cleaned_data["role"] = "student"
        return cleaned_data


class StudentLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg shadow-sm focus:outline-none focus:ring-2 transition duration-150',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-10 py-3 border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg shadow-sm focus:outline-none focus:ring-2 transition duration-150',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )


class InstructorLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-3 border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg shadow-sm focus:outline-none focus:ring-2 transition duration-150',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
            'autofocus': True,
            'type': 'text',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-10 py-3 border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg shadow-sm focus:outline-none focus:ring-2 transition duration-150',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
