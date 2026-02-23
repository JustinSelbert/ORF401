from django.test import TestCase
from django.urls import reverse

from .models import Person


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

  def test_search_matches_state_abbreviation(self):
    response = self.client.get(reverse("rides:index"), {"search": "tx"})
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertEqual(people.first().destination_state, "TX")

  def test_search_matches_destination_city(self):
    response = self.client.get(reverse("rides:index"), {"search": "dallas"})
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertEqual(people.first().destination_city, "Dallas")

  def test_search_matches_origin_and_destination_terms(self):
    response = self.client.get(reverse("rides:index"), {"search": "austin dallas"})
    people = response.context["people"]
    self.assertEqual(people.count(), 1)
    self.assertEqual(people.first().origination, "Austin")
