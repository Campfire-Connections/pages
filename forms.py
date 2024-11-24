from django import forms
from core.models.messaging import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']
