from django import forms
from django.contrib.auth.forms import UserCreationForm

from courses.models import Course


class CourseEnrollForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(CourseEnrollForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()


class StudentsRegistration(UserCreationForm):
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        if role != "student":
            cleaned_data["role"] = "student"
        return cleaned_data
