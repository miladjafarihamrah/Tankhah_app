from django.contrib import admin
from .models import Mission
from .models import Expense
from .models import Balance
from .models import TransactionHistory


admin.site.register(Mission)
admin.site.register(Expense)
admin.site.register(Balance)
admin.site.register(TransactionHistory)

# Register your models here.


