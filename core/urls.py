from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Courses
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.create_course, name='create_course'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/edit/', views.edit_course, name='edit_course'),
    
    # Batches
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.create_batch, name='create_batch'),
    path('batches/<int:id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:id>/edit/', views.edit_batch, name='edit_batch'),
    
    # Exams
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/practice/create/', views.create_practice_paper, name='create_practice_paper'),
    path('exams/mock/create/', views.create_mock_exam, name='create_mock_exam'),
    path('exams/trial/<int:paper_id>/', views.start_trial_exam, name='start_trial_exam'),
    path('exams/start/<str:exam_type>/<int:exam_id>/', views.start_exam, name='start_exam'),
    path('exams/submit/', views.submit_exam, name='submit_exam'),
    path('exams/results/<int:attempt_id>/', views.exam_results, name='exam_results'),
    path('exams/<int:mock_exam_id>/release_results/', views.release_exam_results, name='release_exam_results'),
    path('exams/<int:mock_exam_id>/hide_results/', views.hide_exam_results, name='hide_exam_results'),
    path('exams/trial/results/<int:attempt_id>/', views.trial_results, name='trial_results'),
    path('exams/warning/<int:attempt_id>/', views.report_warning, name='report_warning'),
    
    # Materials
    path('materials/', views.materials_list, name='materials_list'),
    path('materials/upload/', views.upload_material, name='upload_material'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/approval/', views.student_approval, name='student_approval'),
    path('admin/students/approve/<int:student_id>/', views.approve_student, name='approve_student'),
    path('admin/students/disapprove/<int:student_id>/', views.disapprove_student, name='disapprove_student'),
    path('admin/questions/import/', views.import_questions, name='import_questions'),
    path('admin/questions/ai/', views.ai_questions, name='ai_questions'),
    path('admin/questions/', views.question_list, name='question_list'),
    path('admin/questions/create/', views.create_question, name='create_question'),
    path('admin/questions/<int:id>/edit/', views.edit_question, name='edit_question'),
]
