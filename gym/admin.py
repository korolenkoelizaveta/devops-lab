from django.contrib import admin
from gym.models import User, MembershipType, Membership, WorkoutSession

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "phone", "specialization", "account")
    list_filter = ("role",)
    search_fields = ("name", "phone", "specialization") 
    fieldsets = (
        (None, {"fields": ("name", "role", "picture", "account")}),
        ("Дополнительно", {"fields": ("phone", "specialization")}),
    )

@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ("type", "description")
    search_fields = ("type", "description") 

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("client", "membership_type", "is_active")
    list_filter = ("is_active", "membership_type")
    search_fields = ("client__name",)
    autocomplete_fields = ("client", "membership_type")

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("client", "trainer", "session_date")
    list_filter = ("session_date",)
    search_fields = ("client__name", "trainer__name")
    autocomplete_fields = ("client", "trainer")
