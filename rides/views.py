from django.shortcuts import render

from .models import Person

# relative import of forms
from .forms import RideForm

# Create your views here.


def index(request):

  form = RideForm(request.GET or None)
  context = {"form": form, "people": None}

  if "search" in request.GET:
    search = request.GET["search"].strip()
    context["people"] = (
      Person.objects.filter(first_name=search)
      | Person.objects.filter(origination__icontains=search)
    )

  return render(request, "index_view.html", context)
