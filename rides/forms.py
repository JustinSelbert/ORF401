from django import forms

from .models import Person


INPUT_CLASS = "input-field"
SELECT_CLASS = "input-field select-field"


class RideForm(forms.Form):
  search = forms.CharField(
    label="Search rides",
    max_length=64,
    required=False,
    widget=forms.TextInput(
      attrs={
        "placeholder": "e.g. Austin, Dallas, or TX",
        "class": INPUT_CLASS,
        "autocomplete": "off",
      }
    ),
  )
  travel_date = forms.DateField(
    label="Date",
    required=False,
    widget=forms.DateInput(attrs={"type": "date", "class": INPUT_CLASS}),
  )
  minimum_seats = forms.IntegerField(
    label="Minimum seats",
    required=False,
    min_value=1,
    max_value=6,
    widget=forms.NumberInput(
      attrs={"class": INPUT_CLASS, "placeholder": "1", "min": 1, "max": 6}
    ),
  )
  passengers_only = forms.BooleanField(
    label="Only show rides taking passengers",
    required=False,
    initial=True,
    widget=forms.CheckboxInput(attrs={"class": "checkbox-field"}),
  )


class NewRideForm(forms.ModelForm):
  class Meta:
    model = Person
    fields = [
      "first_name",
      "origination",
      "destination_city",
      "destination_state",
      "date",
      "time",
      "taking_passengers",
      "seats_available",
    ]
    widgets = {
      "first_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
      "origination": forms.TextInput(attrs={"class": INPUT_CLASS}),
      "destination_city": forms.TextInput(attrs={"class": INPUT_CLASS}),
      "destination_state": forms.TextInput(
        attrs={"class": INPUT_CLASS, "maxlength": 2}
      ),
      "date": forms.DateInput(attrs={"type": "date", "class": INPUT_CLASS}),
      "time": forms.TimeInput(attrs={"type": "time", "class": INPUT_CLASS}),
      "taking_passengers": forms.CheckboxInput(attrs={"class": "checkbox-field"}),
      "seats_available": forms.NumberInput(
        attrs={"class": INPUT_CLASS, "min": 0, "max": 6}
      ),
    }

  def clean_destination_state(self):
    return self.cleaned_data["destination_state"].upper()


class SignInForm(forms.Form):
  email = forms.EmailField(
    label="Email",
    widget=forms.EmailInput(
      attrs={"class": INPUT_CLASS, "placeholder": "you@example.com"}
    ),
  )
  password = forms.CharField(
    label="Password",
    strip=False,
    widget=forms.PasswordInput(
      attrs={"class": INPUT_CLASS, "placeholder": "Enter your password"}
    ),
  )
  remember_me = forms.BooleanField(
    label="Keep me signed in on this device",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "checkbox-field"}),
  )


class CreateAccountForm(forms.Form):
  first_name = forms.CharField(
    label="First name",
    max_length=64,
    widget=forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "Alex"}),
  )
  email = forms.EmailField(
    label="Email",
    widget=forms.EmailInput(
      attrs={"class": INPUT_CLASS, "placeholder": "alex@example.com"}
    ),
  )
  home_city = forms.CharField(
    label="Home city",
    max_length=64,
    widget=forms.TextInput(
      attrs={"class": INPUT_CLASS, "placeholder": "Austin, TX"}
    ),
  )
  password = forms.CharField(
    label="Create password",
    strip=False,
    widget=forms.PasswordInput(
      attrs={"class": INPUT_CLASS, "placeholder": "8+ characters"}
    ),
  )
  marketing_opt_in = forms.BooleanField(
    label="Send me launch updates and ride credits",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "checkbox-field"}),
  )


class ProfilePreferencesForm(forms.Form):
  music_focus = forms.MultipleChoiceField(
    label="Music and podcast preferences",
    required=False,
    choices=[
      ("indie", "Indie"),
      ("hiphop", "Hip-Hop"),
      ("edm", "EDM"),
      ("podcasts", "Podcasts"),
      ("news", "News"),
      ("audiobooks", "Audiobooks"),
    ],
    widget=forms.SelectMultiple(attrs={"class": SELECT_CLASS, "size": 6}),
  )
  conversation_style = forms.ChoiceField(
    label="Conversation style",
    choices=[
      ("chatty", "Chatty"),
      ("balanced", "Balanced"),
      ("quiet", "Quiet ride"),
    ],
    widget=forms.Select(attrs={"class": SELECT_CLASS}),
  )
  climate_preference = forms.ChoiceField(
    label="Cabin climate",
    choices=[
      ("cool", "Cool"),
      ("neutral", "Neutral"),
      ("warm", "Warm"),
    ],
    widget=forms.Select(attrs={"class": SELECT_CLASS}),
  )
  pet_friendly = forms.BooleanField(
    label="Pet-friendly carpools are okay",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "checkbox-field"}),
  )
  women_only_opt_in = forms.BooleanField(
    label="Prioritize women-only carpools when available",
    required=False,
    widget=forms.CheckboxInput(attrs={"class": "checkbox-field"}),
  )


class SupportRequestForm(forms.Form):
  topic = forms.ChoiceField(
    label="Topic",
    choices=[
      ("billing", "Billing and credits"),
      ("safety", "Safety"),
      ("account", "Account and profile"),
      ("match", "Carpool match quality"),
      ("other", "Other"),
    ],
    widget=forms.Select(attrs={"class": SELECT_CLASS}),
  )
  email = forms.EmailField(
    label="Email",
    widget=forms.EmailInput(
      attrs={"class": INPUT_CLASS, "placeholder": "you@example.com"}
    ),
  )
  message = forms.CharField(
    label="How can we help?",
    max_length=1200,
    widget=forms.Textarea(
      attrs={
        "class": INPUT_CLASS,
        "rows": 5,
        "placeholder": "Tell us what happened and include trip details if relevant.",
      }
    ),
  )
