from django.test import TestCase
from django.urls import reverse

from .models import Person


class PageRenderTests(TestCase):
  def test_public_pages_render(self):
    pages = [
      reverse("rides:home"),
      reverse("rides:index"),
      reverse("rides:map"),
      reverse("rides:faq"),
      reverse("rides:sign_in"),
      reverse("rides:profile"),
    ]

    for page in pages:
      with self.subTest(page=page):
        response = self.client.get(page)
        self.assertEqual(response.status_code, 200)


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
