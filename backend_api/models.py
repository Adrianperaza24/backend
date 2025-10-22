from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class BusStop(models.Model):
    SOURCE_CHOICES = [
        ('Moovit', 'Moovit'),
        ('Settepi', 'Settepi'),
        ('Generated', 'Generated'),
    ]
    stop_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='Generated')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name or self.stop_id}"

class CoverageMesh(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} v{self.version}"

class CoverageMeshPoint(models.Model):
    mesh = models.ForeignKey(CoverageMesh, on_delete=models.CASCADE, related_name='points')
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()
    class Meta:
        ordering = ['order']

class RoutePlan(models.Model):
    route_plan_name = models.CharField(max_length=150)
    bus_supplier = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.route_plan_name} ({'active' if self.is_active else 'inactive'})"

class Route(models.Model):
    SHIFT_CHOICES = [
        ('FIXED_8HRS', 'FIXED_8HRS'),
        ('MIXED_8HRS', 'MIXED_8HRS'),
        ('MIXED_12HRS', 'MIXED_12HRS'),
    ]
    plan = models.ForeignKey(RoutePlan, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=150)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, blank=True)
    color = models.CharField(max_length=7, default="#2E86DE")
    def __str__(self):
        return f"{self.route_name}"

class RouteStopPoint(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=150, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()
    class Meta:
        ordering = ['order']

class RouteTrackPoint(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trackpoints')
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()
    class Meta:
        ordering = ['order']