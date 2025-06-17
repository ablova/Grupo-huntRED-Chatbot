# /home/pablo/app/ats/analytics/models.py
from django.db import models
from django.contrib.auth.models import User

class AnalyticsEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"

class UserMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.metric_name}"

class SystemMetric(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metric_name} - {self.timestamp}"

class Report(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title 