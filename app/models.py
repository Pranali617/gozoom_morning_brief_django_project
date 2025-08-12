from django.db import models


class MorningBrief(models.Model):
    title = models.TextField()
    link = models.TextField()
    image = models.TextField(blank=True, null=True)
    summary = models.TextField()
    category = models.CharField(max_length=255)
    like = models.IntegerField(default=0)
    dislike = models.IntegerField(default=0)
    hours = models.CharField(max_length=10)
    source = models.CharField(max_length=255)
    original_source = models.CharField(max_length=255)
    original_link = models.TextField()
    owner = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)