from django import forms

from .models import Enquiry


class EnquiryForm(forms.ModelForm):
    # Hidden honeypot field: real visitors leave it empty, simple bots fill it in.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Enquiry
        fields = ("name", "phone", "email", "message")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone number", "autocomplete": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email (optional)", "autocomplete": "email"}),
            "message": forms.Textarea(attrs={"placeholder": "How can we help?", "rows": 5}),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Invalid submission.")
        return ""
