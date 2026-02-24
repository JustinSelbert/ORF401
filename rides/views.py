from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.shortcuts import render

from .forms import (
  CreateAccountForm,
  ProfilePreferencesForm,
  RideForm,
  SignInForm,
  SupportRequestForm,
)
from .models import Person

CITY_COORDINATES = {
  ("east palo alto", "ca"): (37.4688, -122.1411),
  ("stanford", "ca"): (37.4275, -122.1697),
  ("san diego", "ca"): (32.7157, -117.1611),
  ("cupertino", "ca"): (37.3229, -122.0322),
  ("portola valley", "ca"): (37.3721, -122.2180),
  ("monte sereno", "ca"): (37.2369, -121.9922),
  ("santa cruz", "ca"): (36.9741, -122.0308),
  ("los altos", "ca"): (37.3852, -122.1141),
  ("torrance", "ca"): (33.8358, -118.3406),
  ("san jose", "ca"): (37.3382, -121.8863),
  ("carmel valley", "ca"): (36.4791, -121.7328),
  ("los altos hills", "ca"): (37.3791, -122.1375),
  ("bakersfield", "ca"): (35.3733, -119.0187),
  ("menlo park", "ca"): (37.4530, -122.1817),
  ("austin", "tx"): (30.2672, -97.7431),
  ("dallas", "tx"): (32.7767, -96.7970),
  ("miami", "fl"): (25.7617, -80.1918),
  ("orlando", "fl"): (28.5383, -81.3792),
  ("seattle", "wa"): (47.6062, -122.3321),
}

STATE_CENTERS = {
  "CA": (36.7783, -119.4179),
  "TX": (31.9686, -99.9018),
  "FL": (27.6648, -81.5158),
  "WA": (47.7511, -120.7401),
}


def _compatibility_score(person):
  score = 72 + ((len(person.first_name) * 3) + (person.seats_available * 4)) % 25
  return f"{score}%"


def _resolve_coordinates(city_name, state_code):
  city = (city_name or "").strip().lower()
  state = (state_code or "").strip().upper()

  if (city, state.lower()) in CITY_COORDINATES:
    return CITY_COORDINATES[(city, state.lower())]

  if state in STATE_CENTERS:
    return STATE_CENTERS[state]

  return None


def home(request):
  today = timezone.localdate()
  all_rides = Person.objects.all()
  upcoming_rides = all_rides.filter(date__gte=today).order_by("date", "time")
  open_rides = upcoming_rides.filter(taking_passengers=True)

  popular_destinations = (
    all_rides.values("destination_city", "destination_state")
    .annotate(total=Count("id"))
    .order_by("-total", "destination_city")[:4]
  )

  featured_matches = []
  for ride in open_rides[:4]:
    featured_matches.append(
      {
        "rider": ride,
        "compatibility": _compatibility_score(ride),
      }
    )

  context = {
    "nav_page": "home",
    "featured_matches": featured_matches,
    "popular_destinations": popular_destinations,
    "stat_total_rides": all_rides.count(),
    "stat_open_rides": open_rides.count(),
    "stat_open_seats": all_rides.aggregate(total=Sum("seats_available"))["total"] or 0,
    "upcoming_preview": upcoming_rides[:5],
  }
  return render(request, "index.html", context)


def index(request):
  form = RideForm(request.GET or None)
  context = {
    "form": form,
    "people": None,
    "search_executed": False,
    "match_count": 0,
    "nav_page": "search",
  }

  if form.is_bound:
    context["search_executed"] = True

    if form.is_valid():
      people = Person.objects.all()
      search = form.cleaned_data["search"].strip()
      travel_date = form.cleaned_data["travel_date"]
      minimum_seats = form.cleaned_data["minimum_seats"]
      passengers_only = form.cleaned_data["passengers_only"]

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

        people = people.filter(query)

      if travel_date:
        people = people.filter(date=travel_date)

      if minimum_seats:
        people = people.filter(seats_available__gte=minimum_seats)

      if passengers_only:
        people = people.filter(taking_passengers=True)

      people = people.order_by("date", "time", "first_name")
      context["people"] = people
      context["match_count"] = people.count()
    else:
      context["people"] = Person.objects.none()

  return render(request, "index_view.html", context)


def sign_in(request):
  login_form = SignInForm(prefix="login")
  register_form = CreateAccountForm(prefix="register")

  login_success = False
  register_success = False
  active_panel = request.GET.get("panel", "login")

  if request.method == "POST":
    action = request.POST.get("action")

    if action == "login":
      active_panel = "login"
      login_form = SignInForm(request.POST, prefix="login")
      register_form = CreateAccountForm(prefix="register")
      if login_form.is_valid():
        login_success = True

    elif action == "register":
      active_panel = "register"
      register_form = CreateAccountForm(request.POST, prefix="register")
      login_form = SignInForm(prefix="login")
      if register_form.is_valid():
        register_success = True

  return render(
    request,
    "sign_in.html",
    {
      "nav_page": "signin",
      "active_panel": active_panel,
      "login_form": login_form,
      "register_form": register_form,
      "login_success": login_success,
      "register_success": register_success,
    },
  )


def profile(request):
  defaults = {
    "music_focus": ["indie", "podcasts"],
    "conversation_style": "balanced",
    "climate_preference": "neutral",
    "pet_friendly": True,
    "women_only_opt_in": False,
  }

  if request.method == "POST":
    form = ProfilePreferencesForm(request.POST)
    preferences_saved = form.is_valid()
    if preferences_saved:
      cleaned = form.cleaned_data
      defaults = {
        "music_focus": cleaned["music_focus"],
        "conversation_style": cleaned["conversation_style"],
        "climate_preference": cleaned["climate_preference"],
        "pet_friendly": cleaned["pet_friendly"],
        "women_only_opt_in": cleaned["women_only_opt_in"],
      }
  else:
    form = ProfilePreferencesForm(initial=defaults)
    preferences_saved = False

  if request.method == "POST" and preferences_saved:
    form = ProfilePreferencesForm(initial=defaults)

  linked_accounts = [
    {
      "name": "Spotify",
      "status": "Connected",
      "detail": "47 shared artists with nearby riders",
    },
    {
      "name": "Instagram",
      "status": "Connected",
      "detail": "Travel and wellness tags enabled for matching",
    },
    {
      "name": "YouTube Music",
      "status": "Not linked",
      "detail": "Connect to improve soundtrack compatibility",
    },
    {
      "name": "LinkedIn",
      "status": "Connected",
      "detail": "Commute cadence boosts weekday pairing accuracy",
    },
  ]

  upcoming_rides = Person.objects.filter(taking_passengers=True).order_by("date", "time")[:4]

  return render(
    request,
    "profile.html",
    {
      "nav_page": "profile",
      "profile_name": "Avery Carter",
      "profile_tier": "SparkRides Plus",
      "profile_city": "Austin, TX",
      "profile_score": "4.9",
      "linked_accounts": linked_accounts,
      "upcoming_rides": upcoming_rides,
      "preferences_form": form,
      "preferences_saved": preferences_saved,
    },
  )


def map_view(request):
  available_rides = Person.objects.filter(taking_passengers=True, seats_available__gt=0).order_by(
    "date", "time"
  )

  map_rides = []
  unresolved_rides = []

  for ride in available_rides:
    origin_coordinates = _resolve_coordinates(ride.origination, ride.destination_state)
    destination_coordinates = _resolve_coordinates(
      ride.destination_city, ride.destination_state
    )

    # If one side cannot be resolved, fall back to the side that is known.
    if not origin_coordinates and destination_coordinates:
      origin_coordinates = destination_coordinates
    if not destination_coordinates and origin_coordinates:
      destination_coordinates = origin_coordinates

    if not origin_coordinates or not destination_coordinates:
      unresolved_rides.append(ride)
      continue

    map_rides.append(
      {
        "id": ride.id,
        "first_name": ride.first_name,
        "origination": ride.origination,
        "destination_city": ride.destination_city,
        "destination_state": ride.destination_state,
        "date": ride.date.isoformat(),
        "time": ride.time.strftime("%H:%M"),
        "seats_available": ride.seats_available,
        "origin_lat": origin_coordinates[0],
        "origin_lng": origin_coordinates[1],
        "destination_lat": destination_coordinates[0],
        "destination_lng": destination_coordinates[1],
      }
    )

  corridors = (
    available_rides.values("origination", "destination_city", "destination_state")
    .annotate(
      total_rides=Count("id"),
      open_seats=Sum("seats_available"),
      active_drivers=Count("id", filter=Q(taking_passengers=True)),
    )
    .order_by("-total_rides", "origination")[:8]
  )

  corridor_cards = []
  for corridor in corridors:
    rides = corridor["total_rides"]
    seats = corridor["open_seats"] or 0

    if rides >= 3:
      load_label = "High demand"
    elif rides == 2:
      load_label = "Steady"
    else:
      load_label = "Light"

    corridor_cards.append(
      {
        "route": (
          f"{corridor['origination']} to "
          f"{corridor['destination_city']}, {corridor['destination_state']}"
        ),
        "load": load_label,
        "rides": rides,
        "open_seats": seats,
        "active_drivers": corridor["active_drivers"],
      }
    )

  pickup_hotspots = (
    available_rides.values("origination")
    .annotate(total=Count("id"))
    .order_by("-total", "origination")[:6]
  )

  plotted_ride_ids = [entry["id"] for entry in map_rides]
  plotted_rides = available_rides.filter(id__in=plotted_ride_ids).order_by("date", "time")

  return render(
    request,
    "map.html",
    {
      "nav_page": "map",
      "map_rides": map_rides,
      "available_rides": plotted_rides,
      "plotted_ride_count": len(map_rides),
      "unresolved_ride_count": len(unresolved_rides),
      "corridor_cards": corridor_cards,
      "pickup_hotspots": pickup_hotspots,
      "network_rides": available_rides.count(),
      "network_seats": available_rides.aggregate(total=Sum("seats_available"))["total"] or 0,
    },
  )


def faq(request):
  faqs = [
    {
      "question": "How does compatibility matching work?",
      "answer": (
        "SparkRides combines route overlap with optional social signals from linked "
        "platforms like Spotify and Instagram. Riders can tune preferences such as "
        "conversation style, music focus, and comfort settings."
      ),
    },
    {
      "question": "Do I need to connect social accounts?",
      "answer": (
        "No. Social linking is optional. You can still use route-based matching only. "
        "Linking profiles improves recommendations and helps identify better carpool "
        "partners."
      ),
    },
    {
      "question": "Can I choose women-only or quiet rides?",
      "answer": (
        "Yes. Profile preferences include women-only priority and quiet-ride matching. "
        "Availability depends on active supply in your area."
      ),
    },
    {
      "question": "What safety checks are in place?",
      "answer": (
        "Every account goes through phone and email verification. Riders can report "
        "issues from each trip card, and support reviews safety submissions quickly."
      ),
    },
    {
      "question": "How do credits and refunds work?",
      "answer": (
        "Trip credits apply automatically at checkout. If a driver cancels before pickup, "
        "you receive an automatic refund or a rebook credit."
      ),
    },
  ]

  form = SupportRequestForm(request.POST or None)
  support_sent = False

  if request.method == "POST" and form.is_valid():
    support_sent = True
    form = SupportRequestForm()

  return render(
    request,
    "faq.html",
    {
      "nav_page": "faq",
      "faqs": faqs,
      "support_form": form,
      "support_sent": support_sent,
    },
  )
