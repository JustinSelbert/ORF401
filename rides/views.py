from django.shortcuts import render
from django.db.models import Q

from .models import Person

# relative import of forms
from .forms import RideForm

# Create your views here.


def index(request):

  form = RideForm(request.GET or None)
  context = {"form": form, "people": None}

  if "search" in request.GET:
    search = request.GET["search"].strip()

    if search:
      terms = search.replace(",", " ").split()
      query = Q()

      for term in terms:
        term_query = (
          Q(first_name__icontains=term)
          | Q(origination__icontains=term)
          | Q(destination_city__icontains=term)
        )

        # Treat 2-character tokens as potential state abbreviations.
        if len(term) == 2:
          term_query = term_query | Q(destination_state__iexact=term)
        else:
          term_query = term_query | Q(destination_state__icontains=term)

        query &= term_query

      context["people"] = Person.objects.filter(query)
    else:
      context["people"] = Person.objects.none()

  return render(request, "index_view.html", context)
