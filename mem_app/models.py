from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Verse(models.Model):
    reference = models.CharField(max_length = 128, unique=True)
    text = models.TextField()
    
class User_verses(models.Model):
    verse_id = models.ForeignKey(Verse, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    score = models.DecimalField(max_digits = 3, decimal_places = 2, default = 0.00)
