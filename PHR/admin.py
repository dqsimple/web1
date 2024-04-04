from django.contrib import admin
from .models import Patient, User, ActionLog


admin.site.register(User)
admin.site.register(Patient)

admin.site.register(ActionLog)

"""
class ActionLogAdmin(admin.ModelAdmin):
    list_display['timestamp', 'user', 'user__username', 'action']
    list_filter['timestamp', 'user']
    search_fields = ['user__username', 'action']
"""

# Register your models here.
