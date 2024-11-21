from django import forms
from .models.messaging import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
