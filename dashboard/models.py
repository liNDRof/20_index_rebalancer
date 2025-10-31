from django.db import models
from django.contrib.auth.models import User

class TraderSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_interval = models.IntegerField(default=3600)
    last_run_time = models.DateTimeField(null=True, blank=True)
    auto_rebalance = models.BooleanField(default=True)

    def __str__(self):
        return f"Налаштування трейдера для {self.user.username}"

