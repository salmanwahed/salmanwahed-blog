from django import forms


class ContactForm(forms.Form):
    """Contact form with a honeypot.

    `website` is invisible to people and empty in a real submission, so anything
    that fills it in is a bot. The field is validated rather than silently
    dropped so the view can decide what to do -- see ContactView.
    """

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    subject = forms.CharField(max_length=150)
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}))

    # Honeypot. aria-hidden and tabindex keep it away from screen readers and
    # keyboard users; the CSS class moves it out of view.
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(
            attrs={
                "class": "honeypot",
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
    )

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write a little more so I know what you need.")
        return message
