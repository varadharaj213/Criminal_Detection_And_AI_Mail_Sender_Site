from django.db import models
from django.utils import timezone
import pytz

class Profile(models.Model):
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    age = models.IntegerField()
    identi = models.CharField(max_length=200)
    nationality = models.CharField(max_length=200)
    crime = models.CharField(max_length=200)
    gender = models.CharField(max_length=200)
    present = models.BooleanField(default=False)
    image = models.ImageField()
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name


class LastFace(models.Model):
    last_face = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    pincode = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.last_face} - {self.city if self.city else 'Unknown Location'}"
    
    def formatted_date(self):
        utc_time = self.date.astimezone(pytz.UTC)
        return utc_time.strftime("%Y-%m-%d %H:%M:%S")


class AudioAlert(models.Model):
    ALERT_TYPES = [
        ('help', 'Help Me'),
        ('save', 'Save Me'),
        ('emergency', 'Emergency'),
        ('danger', 'Danger'),
        ('other', 'Other'),
    ]
    
    detected_text = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    confidence = models.FloatField(default=0.0)
    date = models.DateTimeField(default=timezone.now)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    pincode = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Audio Alert: {self.detected_text[:50]}..."
    
    def formatted_date(self):
        utc_time = self.date.astimezone(pytz.UTC)
        return utc_time.strftime("%Y-%m-%d %H:%M:%S")