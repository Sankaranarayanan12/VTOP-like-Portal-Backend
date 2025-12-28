from django.core.management.base import BaseCommand
from core.models import Enrollment
from django.utils import timezone
class Command(BaseCommand):
    help = "Calculate grades for all enrollments"

    def handle(self, *args, **kwargs):
        enrollments = Enrollment.objects.all()
        count = 0

        for enrollment in enrollments:
            if enrollment.marks is None:
                continue  
            if enrollment.revaluation_deadline and timezone.now() < enrollment.revaluation_deadline:
                continue  
           
            if enrollment.marks >= 90:
                enrollment.grade = "A+"
            elif enrollment.marks >= 80:
                enrollment.grade = "A"
            elif enrollment.marks >= 70:
                enrollment.grade = "B+"
            elif enrollment.marks >= 60:
                enrollment.grade = "B"
            elif enrollment.marks >= 50:
                enrollment.grade = "C"
            else:
                enrollment.grade = "F"

            enrollment.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Grades calculated for {count} enrollments"))
