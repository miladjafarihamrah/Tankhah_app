from django.db import models
from django.contrib.auth.models import User

class Mission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.CharField(max_length=10)  # تاریخ شمسی
    factory = models.CharField(max_length=100)  # کارخانه

    def __str__(self):
        return f"{self.date} - {self.factory}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.CharField(max_length=10)  # تاریخ شمسی
    description = models.TextField()  # توضیحات
    amount = models.IntegerField()  # مبلغ
    factory = models.CharField(max_length=100, blank=True, null=True)  # کارخانه

    def __str__(self):
        return f"{self.date} - {self.description}"
    

class Balance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    amount = models.IntegerField(default=4000000)  # مقدار اولیه 4,000,000 تومان

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_balance(sender, instance, created, **kwargs):
    if created:
        Balance.objects.create(user=instance)

from django.db import models
from django_jalali.db import models as jmodels  # برای تاریخ شمسی

class TransactionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()  # مثبت برای افزایش، منفی برای کاهش
    action = models.CharField(max_length=10)  # 'increase' یا 'decrease'
    date = jmodels.jDateField(auto_now_add=True)  # تاریخ شمسی خودکار
    
    def __str__(self):
        return f"{self.user} - {self.amount} - {self.date}"