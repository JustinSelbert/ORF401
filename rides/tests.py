import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import Person
from .views import ROUTE_COORDINATE_CACHE


class PageRenderTests(TestCase):
  def test_public_pages_render(self):
    pages = [
      reverse("rides:home"),
      reverse("rides:index"),
      reverse("rides:add_ride"),
      reverse("rides:create"),
      reverse("rides:map"),
      reverse("rides:faq"),
      reverse("rides:sign_in"),
      reverse("rides:profile"),
    ]

    for page in pages:
      with self.subTest(page=page):
        response = self.client.get(page)
        self.assertEqual(response.status_code, 200)

  def test_rider_profile_page_renders(self):
    rider = Person.objects.create(
      first_name="Morgan",
      origination="Austin",
      destination_city="Dallas",
      destination_state="TX",
      date="2026-02-25",
      time="09:15",
      taking_passengers=True,
      seats_available=2,
      age=29,
      relationship_status="Single",
      occupation="Product Manager",
      interests="Hiking, Live music, Startups",
      personality_style="Curious, conversational, thoughtful",
      looking_for="Friendship, Networking",
      bio="Coffee-powered builder who loves road trips and ideas.",
    )

    response = self.client.get(reverse("rides:rider_profile", args=[rider.id]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Morgan")


class RideSearchTests(TestCase):
  def setUp(self):
    Person.objects.create(
      first_name="Alex",
      origination="Austin",
      destination_city="Dallas",
      destination_state="TX",
      date="2026-02-23",
      time="09:00",
      taking_passengers=True,
      seats_available=2,
      occupation="Software Engineer",
      interests="Tech, Running, Coffee",
      personality_style="Outgoing and analytical",
      looking_for="Networking, Friendship",
      relationship_status="Single",
    )
    Person.objects.create(
      first_name="Jamie",
      origination="Miami",
      destination_city="Orlando",
      destination_state="FL",
      date="2026-02-24",
      time="10:30",
      taking_passengers=True,
      seats_available=1,
      occupation="Graphic Designer",
      interests="Design, Art, Music",
      personality_style="Calm and creative",
      looking_for="Friendship",
      relationship_status="In a relationship",
    )
    Person.objects.create(
      first_name="Taylor",
      origination="Austin",
      destination_city="Dallas",
      destination_state="TX",
      date="2026-02-23",
      time="12:30",
      taking_passengers=False,
      seats_available=0,
      occupation="Operations Analyst",
      interests="Data, Soccer, Gaming",
      personality_style="Direct and practical",
      looking_for="Networking",
      relationship_status="Single",
    )

  def test_search_matches_state_abbreviation(self):
    response = self.client.get(reverse("rides:index"), {"search": "tx"})
    people = response.context["people"]
    self.assertEqual(people.count(), 2)

  def test_search_matches_destination_city(self):
    response = self.client.get(reverse("rides:index"), {"search": "dallas"})
    people = response.context["people"]
    self.assertEqual(people.count(), 2)

  def test_search_matches_origin_and_destination_terms(self):
    response = self.client.get(reverse("rides:index"), {"search": "austin dallas"})
    people = response.context["people"]
    self.assertEqual(people.count(), 2)

  def test_filter_passengers_only(self):
    response = self.client.get(
      reverse("rides:index"),
      {
        "search": "austin dallas",
        "passengers_only": "on",
      },
    )
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertTrue(people.first().taking_passengers)

  def test_filter_minimum_seats(self):
    response = self.client.get(
      reverse("rides:index"),
      {
        "search": "austin dallas",
        "minimum_seats": 2,
      },
    )
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertEqual(people.first().first_name, "Alex")

  def test_search_matches_interest_term(self):
    response = self.client.get(reverse("rides:index"), {"search": "running"})
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertEqual(people.first().first_name, "Alex")


class RideCreationTests(TestCase):
  def test_create_ride_from_form(self):
    response = self.client.post(
      reverse("rides:add_ride"),
      {
        "first_name": "Riley",
        "origination": "Austin",
        "destination_city": "Dallas",
        "destination_state": "tx",
        "date": "2026-03-03",
        "time": "08:45",
        "taking_passengers": "on",
        "seats_available": "3",
      },
      follow=True,
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(Person.objects.count(), 1)
    ride = Person.objects.first()
    self.assertEqual(ride.first_name, "Riley")
    self.assertEqual(ride.destination_state, "TX")


class _MockResponse:
  def __init__(self, payload):
    self.payload = payload

  def read(self):
    return json.dumps(self.payload).encode("utf-8")

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    return False


class RoadRouteApiTests(TestCase):
  def setUp(self):
    ROUTE_COORDINATE_CACHE.clear()

  @patch("rides.views.urlopen")
  def test_route_api_returns_coordinates_from_geojson(self, mock_urlopen):
    mock_urlopen.return_value = _MockResponse(
      {
        "routes": [
          {
            "geometry": {
              "coordinates": [
                [-122.1411, 37.4688],
                [-121.8863, 37.3382],
              ]
            }
          }
        ]
      }
    )

    response = self.client.get(
      reverse("rides:road_route"),
      {
        "origin_lat": "37.4688",
        "origin_lng": "-122.1411",
        "destination_lat": "37.3382",
        "destination_lng": "-121.8863",
      },
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(
      response.json()["coordinates"],
      [[37.4688, -122.1411], [37.3382, -121.8863]],
    )

  def test_route_api_rejects_invalid_coordinates(self):
    response = self.client.get(
      reverse("rides:road_route"),
      {
        "origin_lat": "95.0",
        "origin_lng": "-122.1411",
        "destination_lat": "37.3382",
        "destination_lng": "-121.8863",
      },
    )

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.json()["error"], "invalid_coordinates")

  @patch("rides.views.urlopen")
  def test_route_api_caches_lookup_results(self, mock_urlopen):
    mock_urlopen.return_value = _MockResponse(
      {
        "routes": [
          {
            "geometry": {
              "coordinates": [
                [-122.1411, 37.4688],
                [-121.8863, 37.3382],
              ]
            }
          }
        ]
      }
    )

    params = {
      "origin_lat": "37.4688",
      "origin_lng": "-122.1411",
      "destination_lat": "37.3382",
      "destination_lng": "-121.8863",
    }
    first_response = self.client.get(reverse("rides:road_route"), params)
    second_response = self.client.get(reverse("rides:road_route"), params)

    self.assertEqual(first_response.status_code, 200)
    self.assertEqual(second_response.status_code, 200)
    self.assertEqual(mock_urlopen.call_count, 1)
