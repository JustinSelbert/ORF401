from django import forms


class RideForm(forms.Form):
  search = forms.CharField(
    label='Search',
    max_length=64,
    required=False,
    widget=forms.TextInput(attrs={"placeholder": "e.g. Zach or Princeton"})
  )
