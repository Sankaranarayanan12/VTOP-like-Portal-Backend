from django.urls import path
from .views import FacultySubjectDetailView,AdminCreateUserView,FacultyViewGrades,SubjectRegistrationView,StudentTimetableView,Faculty_view_enrolled_students,FacultyAddMarksView,StudentMarksView,StudentRevaluationRequestView,AdminRevaluationApprovalView,FacultyMarkAttendanceView,StudentAttendanceView,ParentAttendanceView,FacultyUploadContentView,StudentCourseContentView,AdminCalculateGradesView,ParentTimetableView,ParentMarksView,FacultyUpdateContentView

urlpatterns = [
    path('admin/create-user/', AdminCreateUserView.as_view(), name='admin-create-user'),
     path('subjects/register/<int:subject_id>/',SubjectRegistrationView.as_view(),name='student-subject-register'),
     path('student/timetable/',StudentTimetableView.as_view(),name='student-timetable'),
     path('faculty/subject/<int:subject_id>/students/',Faculty_view_enrolled_students.as_view(), name='faculty-subject-students'),
     path('faculty/marks/add/',FacultyAddMarksView.as_view(),name='faculty-add-marks'),
     path('student/marks/',StudentMarksView.as_view(),name='student-view-marks'),
     path('student/revaluation/request/',StudentRevaluationRequestView.as_view(),name='student-revaluation-request'),
     path('admin/revaluation/approve/',AdminRevaluationApprovalView.as_view(),name='admin-revaluation-approve'),
     path('faculty/attendance/mark/',FacultyMarkAttendanceView.as_view(),name='faculty-mark-attendance'),
     path('student/attendance/',StudentAttendanceView.as_view(),name='student-view-attendance'),
     path('parent/attendance/',ParentAttendanceView.as_view(),name='parent-view-attendance'),
     path('faculty/content/upload/',FacultyUploadContentView.as_view(),name='faculty-upload-content'),
     path('student/content/',StudentCourseContentView.as_view(),name='student-view-content'),
     path('admin/calculate-grades/',AdminCalculateGradesView.as_view(),name='admin-calculate-grades'),
     path('parent/timetable/',ParentTimetableView.as_view(),name='parent-view-timetable'),
     path('parent/marks/',ParentMarksView.as_view(),name='parent-view-marks'),
     path('faculty/content/<int:content_id>/',FacultyUpdateContentView.as_view(),name='faculty-update-content'),
     path('faculty/subject/<int:subject_id>/grades/', FacultyViewGrades.as_view(), name='faculty-view-grades'),
     path('faculty/subject/<int:subject_id>/',FacultySubjectDetailView.as_view(),name='faculty-subject-detail')

]