import unicodecsv as unicodecsv
from django.contrib import admin
from .models import User, TeacherProfile, StudentProfile, GroupAdminForm, Group, StaffProxyModel
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token
import csv
from django.http import HttpResponse

#Register your models here.

class FilterTokenAdmin(admin.ModelAdmin):
    search_fields = ['user__email','user__username']



class AccountAdmin(UserAdmin):
    list_display = ('email','username','date_joined','last_login','is_admin')
    search_fields = ('email','username')
    readonly_fields = ('date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class StudentAdmin(admin.ModelAdmin):
    model = StudentProfile
    search_fields = ['user__email','user__username']

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response


    actions = ["export_as_csv"]


    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class StaffProxyModelAdmin(UserAdmin):

    def export_as_csv_action(description="Export selected objects as CSV file",
                             fields=None, exclude=None, header=True):


        def export_as_csv(modeladmin, request, queryset):
            opts = modeladmin.model._meta

            if not fields:
                field_names = [field.name for field in opts.fields]
            else:
                field_names = fields

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename={}.csv'.format(opts)

            writer = unicodecsv.writer(response, encoding='utf-8')
            if header:
                writer.writerow(field_names)
            for obj in queryset:
                row = [getattr(obj, field)() if callable(getattr(obj, field)) else getattr(obj, field) for field in
                       field_names]
                writer.writerow(row)
            return response

        export_as_csv.short_description = description
        return export_as_csv


    search_fields = ['email', 'username']
    list_display = ('email', 'username', 'telegram_number', 'district', 'phone_no', 'parent_number')
    #actions = ["export_as_csv"]
    actions = [export_as_csv_action("CSV Export", fields=['email', 'username', 'telegram_number', 'district', 'phone_no', 'parent_number'])]



    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(User,AccountAdmin)
admin.site.register(TeacherProfile)
admin.site.register(StudentProfile,StudentAdmin)
admin.site.register(StaffProxyModel,StaffProxyModelAdmin)

# Unregister the original Group admin.
admin.site.unregister(Group)

# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']

# Register the new Group ModelAdmin.
admin.site.register(Group, GroupAdmin)
admin.site.register(Token,FilterTokenAdmin)


