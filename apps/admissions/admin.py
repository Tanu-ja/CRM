from django.contrib import admin

from .models import Admission


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ["admission_number", "lead", "status", "amount", "commission", "created_at"]
    list_filter = ["status"]
    search_fields = ["admission_number", "admission_phone", "student_name"]
    readonly_fields = ["commission"]
