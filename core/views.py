from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsStudent,IsFaculty,IsAdmin,IsParent
from django.shortcuts import get_object_or_404
from .models import Subject,Enrollment,CourseContent
from core.management.commands.calculate_grades import Command
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin
from .models import User
from django.utils import timezone
from datetime import timedelta
class AdminCreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        role = request.data.get('role')
        linked_student_id = request.data.get('linked_student')

        if not all([username, password, email, role]):
            return Response({"error": "username, password, email, and role are required"}, status=status.HTTP_400_BAD_REQUEST)

        if role not in ['Admin', 'Student', 'Faculty', 'Parent']:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'Parent' and linked_student_id is None:
            return Response({"error": "linked_student is required for Parent role"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        linked_student = None
        if linked_student_id:
            try:
                linked_student = User.objects.get(id=linked_student_id, role='Student')
            except User.DoesNotExist:
                return Response({"error": "Linked student not found"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role,
            linked_student=linked_student
        )

        return Response({"message": f"{role} created successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)


class FacultySubjectDetailView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)

        self.check_object_permissions(request, subject)

        return Response({"subject": subject.name})
class SubjectRegistrationView(APIView):
    permission_classes = [IsAuthenticated,IsStudent]

    def post(self, request, subject_id):
        student = request.user
        subject = get_object_or_404(Subject, id=subject_id)
        existing_enrollments = Enrollment.objects.filter(student=student)
        for enrollment in existing_enrollments:
            if enrollment.subject.slot == subject.slot:
                return Response(
                    {"error": "Slot clash detected"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        total_credits = sum(e.subject.credits for e in existing_enrollments)

        if total_credits + subject.credits > 27:
            return Response({"error": "Credit limit exceeded"},status=status.HTTP_400_BAD_REQUEST)
        Enrollment.objects.create(student=student,subject=subject)
        return Response({"message": "Subject registered successfully"},status=status.HTTP_201_CREATED)
class StudentTimetableView(APIView):
        permission_classes = [IsStudent]

        def get(self, request):
            student = request.user
            enrollments = Enrollment.objects.filter(student=student)
            timetable = {}
            for enrollment in enrollments:
                subject = enrollment.subject
                timetable[subject.slot] = {
                "subject": subject.name,
                "faculty": subject.faculty.username
                }
            return Response(timetable)
class Faculty_view_enrolled_students(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]
    def get(self,request,subject_id):
        subject = get_object_or_404(Subject, id=subject_id)
        if subject.faculty != request.user:
            return Response({"error": "Not allowed"}, status=403)
        enrollments = Enrollment.objects.filter(subject=subject)
        students = [{
        "id": e.student.id,
        "username": e.student.username,
        "email": e.student.email
    }
    for e in enrollments]
        return Response({
    "subject": subject.name,
    "students": students
})
    
class FacultyAddMarksView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def post(self, request):
        subject_id = request.data.get('subject_id')
        student_id = request.data.get('student_id')
        marks = request.data.get('marks')

        if subject_id is None or student_id is None or marks is None:
            return Response(
                {"error": "subject_id, student_id, and marks are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        subject = get_object_or_404(Subject, id=subject_id)

        if subject.faculty != request.user:
            return Response(
                {"error": "You are not allowed to modify this subject"},
                status=status.HTTP_403_FORBIDDEN
            )

        enrollment = get_object_or_404(
            Enrollment,
            student_id=student_id,
            subject=subject
        )

        if enrollment.marks is not None and not enrollment.revaluation_approved:
            return Response(
                {"error": "Marks already assigned. Re-evaluation not approved."},
                status=status.HTTP_403_FORBIDDEN
            )

        if enrollment.marks is None:
            enrollment.revaluation_deadline = timezone.now() + timedelta(days=7)
        enrollment.marks = marks
        enrollment.revaluation_requested = False
        enrollment.revaluation_approved = False
        enrollment.save()

        return Response(
            {"message": "Marks updated successfully"},
            status=status.HTTP_200_OK
        )
class StudentMarksView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user

        enrollments = Enrollment.objects.filter(student=student)

        data = []
        for enrollment in enrollments:
            data.append({
                "subject_code": enrollment.subject.code,
                "subject_name": enrollment.subject.name,
                "marks": enrollment.marks,
                "grade": enrollment.grade
            })

        return Response(data)
class StudentRevaluationRequestView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        subject_id = request.data.get('subject_id')
        student = request.user
        
        if not subject_id:
            return Response(
                {"error": "subject_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = get_object_or_404(
            Enrollment,
            student=student,
            subject_id=subject_id
        )
        if enrollment.revaluation_deadline and timezone.now() > enrollment.revaluation_deadline:
            return Response(
        {"error": "Revaluation window closed"},
        status=status.HTTP_400_BAD_REQUEST
    )
        if enrollment.marks is None:
            return Response(
                {"error": "Marks not assigned yet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if enrollment.revaluation_requested:
            return Response(
                {"error": "Re-evaluation already requested"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.revaluation_requested = True
        enrollment.revaluation_approved = False
        enrollment.save()

        return Response(
            {"message": "Re-evaluation request submitted"},
            status=status.HTTP_200_OK
        )
class AdminRevaluationApprovalView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        enrollment_id = request.data.get('enrollment_id')
        approve = request.data.get('approve')

        if enrollment_id is None or approve is None:
            return Response(
                {"error": "enrollment_id and approve are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = get_object_or_404(Enrollment, id=enrollment_id)

        if not enrollment.revaluation_requested:
            return Response(
                {"error": "No re-evaluation requested"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.revaluation_approved = bool(approve)
        enrollment.save()

        return Response(
            {"message": "Re-evaluation decision saved"},
            status=status.HTTP_200_OK
        )
class FacultyMarkAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def post(self, request):
        subject_id = request.data.get('subject_id')
        student_id = request.data.get('student_id')
        attendance = request.data.get('attendance')

        if subject_id is None or student_id is None or attendance is None:
            return Response(
                {"error": "subject_id, student_id and attendance are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = get_object_or_404(Subject, id=subject_id)

        
        if subject.faculty != request.user:
            return Response(
                {"error": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        enrollment = get_object_or_404(
            Enrollment,
            student_id=student_id,
            subject=subject
        )

        enrollment.attendance = attendance
        enrollment.save()

        return Response(
            {"message": "Attendance updated"},
            status=status.HTTP_200_OK
        )
class StudentAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        enrollments = Enrollment.objects.filter(student=student)

        data = []
        for enrollment in enrollments:
            data.append({
                "subject": enrollment.subject.name,
                "attendance": enrollment.attendance
            })

        return Response(data)
class ParentAttendanceView(APIView):
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request):
        student = request.user.linked_student

        if not student:
            return Response(
                {"error": "No student linked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollments = Enrollment.objects.filter(student=student)

        data = []
        for enrollment in enrollments:
            data.append({
                "subject": enrollment.subject.name,
                "attendance": enrollment.attendance
            })

        return Response(data)
class FacultyUploadContentView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def post(self, request):
        subject_id = request.data.get('subject_id')
        title = request.data.get('title')
        description = request.data.get('description', '')
        content_link = request.data.get('content_link', '')

        if not subject_id or not title:
            return Response(
                {"error": "subject_id and title are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = get_object_or_404(Subject, id=subject_id)

        if subject.faculty != request.user:
            return Response(
                {"error": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        CourseContent.objects.create(
            subject=subject,
            title=title,
            description=description,
            content_link=content_link
        )

        return Response(
            {"message": "Content uploaded successfully"},
            status=status.HTTP_201_CREATED
        )
class StudentCourseContentView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        enrollments = Enrollment.objects.filter(student=student)

        subjects = [e.subject for e in enrollments]

        contents = CourseContent.objects.filter(subject__in=subjects)

        data = []
        for content in contents:
            data.append({
                "subject": content.subject.name,
                "title": content.title,
                "description": content.description,
                "link": content.content_link,
                "uploaded_at": content.created_at
            })

        return Response(data)
class AdminCalculateGradesView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        Command().handle()
        return Response(
            {"message": "Grades calculated successfully"},
            status=status.HTTP_200_OK
        )
class ParentTimetableView(APIView):
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request):
        student = request.user.linked_student

        if not student:
            return Response(
                {"error": "No student linked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollments = Enrollment.objects.filter(student=student)
        timetable = {}
        for enrollment in enrollments:
            subject = enrollment.subject
            timetable[subject.slot] = {
                "subject": subject.name,
                "faculty": subject.faculty.username
            }

        return Response(timetable)
class ParentMarksView(APIView):
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request):
        student = request.user.linked_student

        if not student:
            return Response(
                {"error": "No student linked"},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollments = Enrollment.objects.filter(student=student)
        data = []
        for e in enrollments:
            data.append({
                "subject_code": e.subject.code,
                "subject_name": e.subject.name,
                "marks": e.marks,
                "grade": e.grade
            })

        return Response(data)
class FacultyUpdateContentView(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def put(self, request, content_id):
        content = get_object_or_404(CourseContent, id=content_id)

        if content.subject.faculty != request.user:
            return Response({"error": "Not allowed"}, status=403)

        content.title = request.data.get('title', content.title)
        content.description = request.data.get('description', content.description)
        content.content_link = request.data.get('content_link', content.content_link)
        content.save()

        return Response({"message": "Content updated successfully"})

    def delete(self, request, content_id):
        content = get_object_or_404(CourseContent, id=content_id)

        if content.subject.faculty != request.user:
            return Response({"error": "Not allowed"}, status=403)

        content.delete()
        return Response({"message": "Content deleted successfully"})
class FacultyViewGrades(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request, subject_id):
        subject = get_object_or_404(Subject, id=subject_id)

        if subject.faculty != request.user:
            return Response({"error": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)

        enrollments = Enrollment.objects.filter(subject=subject)
        data = []
        for e in enrollments:
            data.append({
                "student_id": e.student.id,
                "username": e.student.username,
                "marks": e.marks,
                "grade": e.grade
            })

        return Response({
            "subject": subject.name,
            "grades": data
        })
