from django.forms.models import inlineformset_factory
from django import forms

from .models import Course, Module

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Contoh: Pengenalan Python, Advanced JavaScript, dll'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none',
                'rows': 4,
                'placeholder': 'Jelaskan apa yang akan dipelajari di modul ini...'
            })
        }

ModuleFormSets = inlineformset_factory(
    Course,
    Module,
    form=ModuleForm,
    extra=2,
    can_delete=True,
    can_delete_extra=True
)

