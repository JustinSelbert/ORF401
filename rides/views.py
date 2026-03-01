import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

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
  ("south san francisco", "ca"): (37.6547, -122.4077),
  ("riverside", "ca"): (33.9806, -117.3755),
  ("mountain view", "ca"): (37.3861, -122.0839),
  ("santa rosa", "ca"): (38.4405, -122.7144),
  ("merced", "ca"): (37.3022, -120.4829),
  ("oakland", "ca"): (37.8044, -122.2711),
  ("san carlos", "ca"): (37.5072, -122.2605),
}

STATE_CENTERS = {
  "CA": (36.7783, -119.4179),
  "TX": (31.9686, -99.9018),
  "FL": (27.6648, -81.5158),
  "WA": (47.7511, -120.7401),
}

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving/"
ROUTE_COORDINATE_CACHE = {}


def _split_csv(value):
  return [item.strip() for item in (value or "").split(",") if item.strip()]


def _compatibility_score(person):
  profile_bonus = min(12, len(_split_csv(person.interests)) * 2)
  intent_bonus = 4 if person.looking_for else 0
  seats_bonus = min(8, person.seats_available * 2)
  score = min(98, 68 + profile_bonus + intent_bonus + seats_bonus)
  return f"{score}%"


def _resolve_coordinates(city_name, state_code):
  city = (city_name or "").strip().lower()
  state = (state_code or "").strip().upper()

  if (city, state.lower()) in CITY_COORDINATES:
    return CITY_COORDINATES[(city, state.lower())]

  if state in STATE_CENTERS:
    return STATE_CENTERS[state]

  return None


def _build_route_key(origin, destination):
  return (
    f"{origin[0]:.5f}|{origin[1]:.5f}|"
    f"{destination[0]:.5f}|{destination[1]:.5f}"
  )


def _decode_polyline(encoded_path, precision=5):
  if not encoded_path:
    return []

  factor = 10 ** precision
  latitude = 0
  longitude = 0
  index = 0
  points = []

  try:
    while index < len(encoded_path):
      result = 1
      shift = 0
      while True:
        byte = ord(encoded_path[index]) - 63 - 1
        index += 1
        result += byte << shift
        shift += 5
        if byte < 0x1f:
          break
      latitude += ~(result >> 1) if (result & 1) else (result >> 1)

      result = 1
      shift = 0
      while True:
        byte = ord(encoded_path[index]) - 63 - 1
        index += 1
        result += byte << shift
        shift += 5
        if byte < 0x1f:
          break
      longitude += ~(result >> 1) if (result & 1) else (result >> 1)

      points.append([latitude / factor, longitude / factor])
  except (IndexError, TypeError):
    return []

  return points


def _normalize_route_coordinates(raw_coordinates):
  coordinates = []
  for point in raw_coordinates:
    if not isinstance(point, (list, tuple)) or len(point) < 2:
      continue

    try:
      longitude = float(point[0])
      latitude = float(point[1])
    except (TypeError, ValueError):
      continue

    coordinates.append([latitude, longitude])

  return coordinates


def _extract_route_coordinates(route):
  if not isinstance(route, dict):
    return None

  geometry = route.get("geometry")

  if isinstance(geometry, dict):
    coordinates = _normalize_route_coordinates(geometry.get("coordinates") or [])
    return coordinates if len(coordinates) > 1 else None

  if isinstance(geometry, str):
    for precision in (5, 6):
      decoded = _decode_polyline(geometry, precision=precision)
      if len(decoded) > 1:
        return decoded

  return None


def _fetch_road_route(origin, destination):
  key = _build_route_key(origin, destination)
  if key in ROUTE_COORDINATE_CACHE:
    return ROUTE_COORDINATE_CACHE[key]

  request_url = (
    f"{OSRM_BASE_URL}{origin[1]},{origin[0]};{destination[1]},{destination[0]}?"
    + urlencode({"overview": "full", "geometries": "geojson"})
  )
  request = Request(
    request_url,
    headers={"User-Agent": "HandyRides/1.0"},
  )

  try:
    with urlopen(request, timeout=8) as response:
      payload = json.loads(response.read().decode("utf-8"))
  except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
    ROUTE_COORDINATE_CACHE[key] = None
    return None

  route = (payload.get("routes") or [None])[0] if isinstance(payload, dict) else None
  coordinates = _extract_route_coordinates(route)
  ROUTE_COORDINATE_CACHE[key] = coordinates
  return coordinates


def _valid_lat_lng(latitude, longitude):
  return -90 <= latitude <= 90 and -180 <= longitude <= 180


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
            | Q(occupation__icontains=term)
            | Q(interests__icontains=term)
            | Q(personality_style__icontains=term)
            | Q(looking_for__icontains=term)
            | Q(relationship_status__icontains=term)
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
      "detail": "47 shared artists with people on your top routes",
    },
    {
      "name": "Instagram",
      "status": "Connected",
      "detail": "Interest tags sharpen your friendship and dating matches",
    },
    {
      "name": "YouTube Music",
      "status": "Not linked",
      "detail": "Connect to boost long-ride conversation fit",
    },
    {
      "name": "LinkedIn",
      "status": "Connected",
      "detail": "Commute patterns improve professional networking matches",
    },
  ]

  upcoming_rides = Person.objects.filter(taking_passengers=True).order_by("date", "time")[:4]

  return render(
    request,
    "profile.html",
    {
      "nav_page": "profile",
      "profile_name": "Justin Selbert",
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
        "occupation": ride.occupation,
        "looking_for": ride.looking_for,
        "origination": ride.origination,
        "destination_city": ride.destination_city,
        "destination_state": ride.destination_state,
        "date": ride.date.isoformat(),
        "time": ride.time.strftime("%H:%M"),
        "seats_available": ride.seats_available,
        "rider_profile_url": reverse("rides:rider_profile", args=[ride.id]),
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


def road_route(request):
  try:
    origin_lat = float(request.GET.get("origin_lat", ""))
    origin_lng = float(request.GET.get("origin_lng", ""))
    destination_lat = float(request.GET.get("destination_lat", ""))
    destination_lng = float(request.GET.get("destination_lng", ""))
  except (TypeError, ValueError):
    return JsonResponse({"coordinates": None, "error": "invalid_coordinates"}, status=400)

  if not _valid_lat_lng(origin_lat, origin_lng) or not _valid_lat_lng(
    destination_lat, destination_lng
  ):
    return JsonResponse({"coordinates": None, "error": "invalid_coordinates"}, status=400)

  origin = [origin_lat, origin_lng]
  destination = [destination_lat, destination_lng]

  if origin == destination:
    return JsonResponse({"coordinates": [origin, destination]})

  coordinates = _fetch_road_route(origin, destination)
  return JsonResponse({"coordinates": coordinates})


def rider_profile(request, person_id):
  rider = get_object_or_404(Person, pk=person_id)
  rider_interests = _split_csv(rider.interests)
  rider_intents = _split_csv(rider.looking_for)

  similar_riders = (
    Person.objects.filter(
      destination_city=rider.destination_city,
      destination_state=rider.destination_state,
      taking_passengers=True,
      seats_available__gt=0,
    )
    .exclude(pk=rider.pk)
    .order_by("date", "time")[:4]
  )

  return render(
    request,
    "rider_profile.html",
    {
      "nav_page": "search",
      "rider": rider,
      "rider_interests": rider_interests,
      "rider_intents": rider_intents,
      "compatibility_score": _compatibility_score(rider),
      "similar_riders": similar_riders,
    },
  )


def faq(request):
  faqs = [
    {
      "question": "How does compatibility matching work?",
      "answer": (
        "SparkRides blends route overlap with optional social signals to rank people you "
        "are more likely to click with. You can optimize for friendships, networking, "
        "romance, and ride comfort."
      ),
    },
    {
      "question": "Do I need to connect social accounts?",
      "answer": (
        "No. You can use SparkRides with route-only matching. Connecting accounts simply "
        "adds richer context so your suggestions feel more human and less random."
      ),
    },
    {
      "question": "Can I choose women-only or quiet rides?",
      "answer": (
        "Yes. Set women-only priority, conversation style, and comfort preferences in your "
        "profile. Availability depends on live supply in your area."
      ),
    },
    {
      "question": "What safety checks are in place?",
      "answer": (
        "Every account is phone and email verified. You can report issues from any trip "
        "card, and safety submissions are prioritized by support."
      ),
    },
    {
      "question": "How do credits and refunds work?",
      "answer": (
        "Trip credits apply automatically at checkout. If a driver cancels before pickup, "
        "you get an automatic refund or instant rebook credit."
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
