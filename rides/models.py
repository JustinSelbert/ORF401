from django.db import models

# Create your models here.


class Person(models.Model):
  first_name = models.CharField(max_length=64)
  origination = models.CharField(max_length=64)
  destination_city = models.CharField(max_length=64)
  destination_state = models.CharField(max_length=2)
  date = models.DateField()
  time = models.TimeField()
  taking_passengers = models.BooleanField(default=False)
  seats_available = models.IntegerField(default=0)
  age = models.PositiveSmallIntegerField(null=True, blank=True)
  relationship_status = models.CharField(max_length=40, blank=True, default="")
  occupation = models.CharField(max_length=120, blank=True, default="")
  interests = models.CharField(max_length=280, blank=True, default="")
  personality_style = models.CharField(max_length=120, blank=True, default="")
  looking_for = models.CharField(max_length=180, blank=True, default="")
  bio = models.TextField(blank=True, default="")

  def __str__(self):
    return f"{self.first_name}: {self.origination} to {self.destination_city}, {self.destination_state}"
