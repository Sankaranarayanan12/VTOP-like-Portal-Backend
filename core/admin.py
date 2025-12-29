from django.contrib import admin
from .models import User,Subject,Enrollment

admin.site.register(User)
admin.site.register(Subject)
admin.site.register(Enrollment)

