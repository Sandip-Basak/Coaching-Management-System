import os
import json
import random
import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import uuid

from .models import (
    User, StudentProfile, Course, Batch, Question, Option,
    PracticePaper, MockExam, Attempt, Answer, CourseMaterial
)
from .forms import (
    SignUpForm, LoginForm, ProfileUpdateForm, CourseForm, BatchForm,
    QuestionForm, OptionFormSet, PracticePaperForm, MockExamForm,
    ImportQuestionsForm, AIQuestionsForm, CourseMaterialForm
)
from .utils import get_student_batches, calculate_score, generate_ai_questions


def home(request):
    """Home page view"""
    courses = Course.objects.all()[:5]  # Limited to 5 for homepage display
    practice_papers = PracticePaper.objects.filter(allowed_for_trial=True)[:5]
    
    context = {
        'courses': courses,
        'practice_papers': practice_papers,
    }
    return render(request, 'home.html', context)


def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Create student profile
            profile = StudentProfile.objects.create(
                user=user,
                profile_photo=form.cleaned_data.get('profile_photo')
            )
            messages.success(request, 'Account created successfully! Please wait for admin approval.')
            return redirect('login')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    """Login view"""
    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Check if user is a student and if they're approved
            if hasattr(user, 'student_profile'):
                if not user.student_profile.approved:
                    messages.error(request, 'Your account is awaiting admin approval.')
                    return render(request, 'registration/login.html', {'form': form})
            
            login(request, user)
            
            # Update session token for single device enforcement
            if hasattr(user, 'student_profile'):
                user.student_profile.session_token = uuid.uuid4()
                user.student_profile.device_identifier = request.META.get('HTTP_USER_AGENT', '')
                user.student_profile.save()
                
                # Store session token in session
                request.session['session_token'] = str(user.student_profile.session_token)
            
            next_url = request.GET.get('next', reverse('dashboard'))
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user
    
    if user.is_admin_staff or user.is_staff:
        # Admin dashboard
        return admin_dashboard(request)
    else:
        # Student dashboard
        student_batches = get_student_batches(user)
        
        # Get all attempts by the student
        attempts = Attempt.objects.filter(user=user).order_by('-start_time')
        
        # Get courses related to the student's batches
        course_ids = student_batches.values_list('course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=course_ids)
        
        # Get practice papers and mock exams for the student's courses
        practice_papers = PracticePaper.objects.filter(course__in=courses)
        mock_exams = MockExam.objects.filter(course__in=courses)
        
        # Get upcoming exams (mock exams with no attempts yet)
        attempted_mock_ids = attempts.filter(attempt_type='mock').values_list('mock_exam_id', flat=True)
        upcoming_exams = mock_exams.exclude(id__in=attempted_mock_ids)
        
        context = {
            'student_batches': student_batches,
            'courses': courses,
            'practice_papers': practice_papers,
            'mock_exams': mock_exams,
            'attempts': attempts[:5],  # Latest 5 attempts
            'upcoming_exams': upcoming_exams,
        }
        return render(request, 'dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    # Get counts for dashboard stats
    pending_approvals = StudentProfile.objects.filter(approved=False).count()
    total_students = StudentProfile.objects.filter(approved=True).count()
    total_courses = Course.objects.count()
    total_batches = Batch.objects.count()
    total_practice_papers = PracticePaper.objects.count()
    total_mock_exams = MockExam.objects.count()
    total_questions = Question.objects.count()
    
    # Get recent activities
    recent_attempts = Attempt.objects.all().order_by('-start_time')[:10]
    recent_materials = CourseMaterial.objects.order_by('-uploaded_at')[:10]
    
    context = {
        'pending_approvals': pending_approvals,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_batches': total_batches,
        'total_practice_papers': total_practice_papers,
        'total_mock_exams': total_mock_exams,
        'total_questions': total_questions,
        'recent_attempts': recent_attempts,
        'recent_materials': recent_materials,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def student_approval(request):
    """Student approval view for admins"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    pending_students = StudentProfile.objects.filter(approved=False)
    approved_students = StudentProfile.objects.filter(approved=True)
    
    context = {
        'pending_students': pending_students,
        'approved_students': approved_students,
    }
    return render(request, 'admin/student_approval.html', context)


@login_required
@require_POST
def approve_student(request, student_id):
    """Approve a student"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to perform this action.")
    
    student_profile = get_object_or_404(StudentProfile, id=student_id)
    student_profile.approved = True
    student_profile.save()
    
    messages.success(request, f"Student {student_profile.user.username} has been approved.")
    return redirect('student_approval')


@login_required
@require_POST
def disapprove_student(request, student_id):
    """Disapprove a student"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to perform this action.")
    
    student_profile = get_object_or_404(StudentProfile, id=student_id)
    student_profile.approved = False
    student_profile.save()
    
    messages.success(request, f"Student {student_profile.user.username} has been disapproved.")
    return redirect('student_approval')


@login_required
def course_list(request):
    """List all courses"""
    user = request.user
    
    if user.is_admin_staff or user.is_staff:
        # Admin can see all courses
        courses = Course.objects.all()
    else:
        # Students see only their enrolled courses
        student_batches = get_student_batches(user)
        course_ids = student_batches.values_list('course_id', flat=True).distinct()
        courses = Course.objects.filter(id__in=course_ids)
    
    paginator = Paginator(courses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'courses/list.html', {'page_obj': page_obj})


@login_required
def course_detail(request, slug):
    """Course detail view"""
    course = get_object_or_404(Course, slug=slug)
    user = request.user
    
    # Check access permission for students
    if not user.is_admin_staff and not user.is_staff:
        # Students can only access their enrolled courses
        student_batches = get_student_batches(user)
        if not student_batches.filter(course=course).exists():
            return HttpResponseForbidden("You do not have access to this course.")
    
    batches = course.batches.all()
    practice_papers = course.practice_papers.all()
    mock_exams = course.mock_exams.all()
    
    context = {
        'course': course,
        'batches': batches,
        'practice_papers': practice_papers,
        'mock_exams': mock_exams,
    }
    return render(request, 'courses/detail.html', context)


@login_required
def create_course(request):
    """Create a new course"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create courses.")
    
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.name}' created successfully.")
            return redirect('course_list')
    else:
        form = CourseForm()
    
    return render(request, 'courses/create.html', {'form': form})


@login_required
def edit_course(request, slug):
    """Edit an existing course"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to edit courses.")
    
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.name}' updated successfully.")
            return redirect('course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/edit.html', {'form': form, 'course': course})


@login_required
def batch_list(request):
    """List all batches"""
    user = request.user
    
    if user.is_admin_staff or user.is_staff:
        # Admin can see all batches
        batches = Batch.objects.all()
    else:
        # Students see only their enrolled batches
        student_batches = get_student_batches(user)
        batches = student_batches
    
    paginator = Paginator(batches, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'batches/list.html', {'page_obj': page_obj})


@login_required
def batch_detail(request, id):
    """Batch detail view"""
    batch = get_object_or_404(Batch, id=id)
    user = request.user
    
    # Check access permission for students
    if not user.is_admin_staff and not user.is_staff:
        # Students can only access their enrolled batches
        student_profile = get_object_or_404(StudentProfile, user=user)
        if not student_profile.batches.filter(id=batch.id).exists():
            return HttpResponseForbidden("You do not have access to this batch.")
    
    # Get materials for this batch
    materials = batch.materials.all()
    students = batch.students.all()
    
    context = {
        'batch': batch,
        'materials': materials,
        'students': students,
    }
    return render(request, 'batches/detail.html', context)


@login_required
def create_batch(request):
    """Create a new batch"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create batches.")
    
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.name}' created successfully.")
            return redirect('batch_list')
    else:
        form = BatchForm()
    
    return render(request, 'batches/create.html', {'form': form})


@login_required
def edit_batch(request, id):
    """Edit an existing batch"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to edit batches.")
    
    batch = get_object_or_404(Batch, id=id)
    
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.name}' updated successfully.")
            return redirect('batch_detail', id=batch.id)
    else:
        form = BatchForm(instance=batch)
    
    return render(request, 'batches/edit.html', {'form': form, 'batch': batch})


@login_required
def exam_list(request):
    """List practice papers and mock exams"""
    user = request.user
    
    if user.is_admin_staff or user.is_staff:
        # Admin can see all exams
        practice_papers = PracticePaper.objects.all()
        mock_exams = MockExam.objects.all()
    else:
        # Students see only exams for their enrolled courses
        student_batches = get_student_batches(user)
        course_ids = student_batches.values_list('course_id', flat=True).distinct()
        practice_papers = PracticePaper.objects.filter(course__id__in=course_ids)
        mock_exams = MockExam.objects.filter(course__id__in=course_ids)
    
    context = {
        'practice_papers': practice_papers,
        'mock_exams': mock_exams,
    }
    return render(request, 'exams/list.html', context)


@login_required
def create_practice_paper(request):
    """Create a new practice paper"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create practice papers.")
    
    if request.method == 'POST':
        form = PracticePaperForm(request.POST)
        if form.is_valid():
            practice_paper = form.save(commit=False)
            practice_paper.created_by = request.user
            practice_paper.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f"Practice Paper '{practice_paper.name}' created successfully.")
            return redirect('exam_list')
    else:
        form = PracticePaperForm()
    
    return render(request, 'exams/create_practice_paper.html', {'form': form})


@login_required
def create_mock_exam(request):
    """Create a new mock exam"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create mock exams.")
    
    if request.method == 'POST':
        form = MockExamForm(request.POST)
        if form.is_valid():
            mock_exam = form.save(commit=False)
            mock_exam.created_by = request.user
            mock_exam.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f"Mock Exam '{mock_exam.name}' created successfully.")
            return redirect('exam_list')
    else:
        form = MockExamForm()
    
    return render(request, 'exams/create_mock_exam.html', {'form': form})


def start_trial_exam(request, paper_id):
    """Start a trial practice paper for non-authenticated users"""
    practice_paper = get_object_or_404(PracticePaper, id=paper_id, allowed_for_trial=True)
    
    # Create a new attempt for the trial
    attempt = Attempt.objects.create(
        attempt_type='practice',
        practice_paper=practice_paper,
        is_trial=True,
        status='in_progress'
    )
    
    # Get a subset of questions for the trial
    all_questions = list(practice_paper.questions.all())
    trial_question_count = min(practice_paper.trial_question_count, len(all_questions))
    trial_questions = random.sample(all_questions, trial_question_count)
    
    # Store question IDs in the session
    request.session['trial_question_ids'] = [q.id for q in trial_questions]
    request.session['trial_attempt_id'] = attempt.id
    
    # Calculate expected end time
    end_time = timezone.now() + timedelta(minutes=practice_paper.time_limit)
    request.session['trial_end_time'] = end_time.isoformat()
    
    context = {
        'paper': practice_paper,
        'questions': trial_questions,
        'attempt': attempt,
        'end_time': end_time,
        'is_trial': True,
    }
    return render(request, 'exams/take_exam.html', context)


@login_required
def start_exam(request, exam_type, exam_id):
    """Start a practice paper or mock exam for authenticated users"""
    user = request.user
    
    if exam_type == 'practice':
        exam = get_object_or_404(PracticePaper, id=exam_id)
        # Check if user is enrolled in the course
        student_batches = get_student_batches(user)
        if not student_batches.filter(course=exam.course).exists():
            return HttpResponseForbidden("You do not have access to this practice paper.")
        
        # Create a new attempt
        attempt = Attempt.objects.create(
            user=user,
            attempt_type='practice',
            practice_paper=exam,
            status='in_progress'
        )
        
        questions = exam.questions.all()
        end_time = timezone.now() + timedelta(minutes=exam.time_limit)
        
    elif exam_type == 'mock':
        exam = get_object_or_404(MockExam, id=exam_id)
        # Check if user is enrolled in the course
        student_batches = get_student_batches(user)
        if not student_batches.filter(course=exam.course).exists():
            return HttpResponseForbidden("You do not have access to this mock exam.")
        
        # Check if user has already attempted this mock exam
        if Attempt.objects.filter(user=user, mock_exam=exam).exists():
            messages.error(request, "You have already attempted this mock exam.")
            return redirect('exam_list')
        
        # Create a new attempt
        attempt = Attempt.objects.create(
            user=user,
            attempt_type='mock',
            mock_exam=exam,
            status='in_progress'
        )
        
        questions = exam.questions.all()
        end_time = timezone.now() + timedelta(minutes=exam.time_limit)
    
    else:
        return HttpResponseForbidden("Invalid exam type.")
    
    context = {
        'paper': exam,
        'questions': questions,
        'attempt': attempt,
        'end_time': end_time,
        'is_trial': False,
        'exam_type': exam_type
    }
    return render(request, 'exams/take_exam.html', context)


@require_POST
def submit_exam(request):
    """Submit an exam attempt"""
    if request.user.is_authenticated:
        # Authenticated user
        attempt_id = request.POST.get('attempt_id')
        attempt = get_object_or_404(Attempt, id=attempt_id)
        
        # Verify the attempt belongs to the user
        if attempt.user != request.user:
            return HttpResponseForbidden("This attempt does not belong to you.")
    else:
        # Trial user
        attempt_id = request.session.get('trial_attempt_id')
        if not attempt_id:
            return HttpResponseForbidden("No trial attempt found.")
        
        attempt = get_object_or_404(Attempt, id=attempt_id, user=None, is_trial=True)
    
    # Parse answers from the form
    answers_data = {}
    for key, value in request.POST.items():
        if key.startswith('question_'):
            question_id = key.replace('question_', '')
            
            # Handle multiple selection (checkboxes)
            if isinstance(value, list):
                answers_data[question_id] = value
            else:
                answers_data[question_id] = [value]
    
    # Save answers
    for question_id, option_ids in answers_data.items():
        question = get_object_or_404(Question, id=question_id)
        answer = Answer.objects.create(
            attempt=attempt,
            question=question
        )
        
        for option_id in option_ids:
            option = get_object_or_404(Option, id=option_id)
            answer.selected_options.add(option)
    
    # Mark attempt as completed
    attempt.status = 'completed'
    attempt.end_time = timezone.now()
    
    # Calculate score
    score = calculate_score(attempt)
    attempt.score = score
    attempt.save()
    
    if request.user.is_authenticated:
        return redirect('exam_results', attempt_id=attempt.id)
    else:
        return redirect('trial_results', attempt_id=attempt.id)


@login_required
def exam_results(request, attempt_id):
    """View results of an exam attempt for authenticated users"""
    attempt = get_object_or_404(Attempt, id=attempt_id)
    
    # Verify the attempt belongs to the user or user is admin
    if attempt.user != request.user and not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to view these results.")
    
    # For mock exams, check if results are released
    if attempt.attempt_type == 'mock' and attempt.mock_exam and not attempt.mock_exam.results_released:
        if not request.user.is_admin_staff and not request.user.is_staff:
            return render(request, 'exams/results_pending.html', {'attempt': attempt})
    
    # Get answers for the attempt
    answers = attempt.answers.all().prefetch_related('question', 'selected_options')
    
    # Organize answers by question with correct/incorrect status
    results = []
    total_marks = 0
    scored_marks = 0
    
    for answer in answers:
        question = answer.question
        selected_options = answer.selected_options.all()
        correct_options = question.options.filter(is_correct=True)
        
        is_correct = False
        if question.multiple_correct:
            # All correct options must be selected and no incorrect ones
            selected_correct = set(opt.id for opt in selected_options if opt.is_correct)
            all_correct = set(opt.id for opt in correct_options)
            selected_incorrect = set(opt.id for opt in selected_options if not opt.is_correct)
            
            is_correct = (selected_correct == all_correct) and not selected_incorrect
        else:
            # Single correct answer - one option must be selected and it must be correct
            is_correct = (len(selected_options) == 1) and selected_options.first().is_correct
        
        question_score = question.marks if is_correct else 0
        total_marks += question.marks
        scored_marks += question_score
        
        results.append({
            'question': question,
            'selected_options': selected_options,
            'correct_options': correct_options,
            'is_correct': is_correct,
            'score': question_score,
            'max_score': question.marks
        })
    
    context = {
        'attempt': attempt,
        'results': results,
        'total_marks': total_marks,
        'scored_marks': scored_marks,
        'percentage': (scored_marks / total_marks * 100) if total_marks > 0 else 0
    }
    return render(request, 'exams/results.html', context)


def trial_results(request, attempt_id):
    """View results of a trial exam attempt for non-authenticated users"""
    attempt = get_object_or_404(Attempt, id=attempt_id, user=None, is_trial=True)
    
    # Verify the attempt ID matches the one in session
    if str(attempt.id) != str(request.session.get('trial_attempt_id')):
        return HttpResponseForbidden("You do not have permission to view these results.")
    
    # Get answers for the attempt
    answers = attempt.answers.all().prefetch_related('question', 'selected_options')
    
    # Organize answers by question with correct/incorrect status
    results = []
    total_marks = 0
    scored_marks = 0
    
    for answer in answers:
        question = answer.question
        selected_options = answer.selected_options.all()
        correct_options = question.options.filter(is_correct=True)
        
        is_correct = False
        if question.multiple_correct:
            # All correct options must be selected and no incorrect ones
            selected_correct = set(opt.id for opt in selected_options if opt.is_correct)
            all_correct = set(opt.id for opt in correct_options)
            selected_incorrect = set(opt.id for opt in selected_options if not opt.is_correct)
            
            is_correct = (selected_correct == all_correct) and not selected_incorrect
        else:
            # Single correct answer - one option must be selected and it must be correct
            is_correct = (len(selected_options) == 1) and selected_options.first().is_correct
        
        question_score = question.marks if is_correct else 0
        total_marks += question.marks
        scored_marks += question_score
        
        results.append({
            'question': question,
            'selected_options': selected_options,
            'correct_options': correct_options,
            'is_correct': is_correct,
            'score': question_score,
            'max_score': question.marks
        })
    
    context = {
        'attempt': attempt,
        'results': results,
        'total_marks': total_marks,
        'scored_marks': scored_marks,
        'percentage': (scored_marks / total_marks * 100) if total_marks > 0 else 0,
        'is_trial': True
    }
    return render(request, 'exams/results.html', context)


@login_required
def report_warning(request, attempt_id):
    """Report a warning for an exam attempt (tab switch, blur, etc.)"""
    if request.method == 'POST':
        attempt = get_object_or_404(Attempt, id=attempt_id)
        
        # Increment warning count
        attempt.warning_count += 1
        attempt.save()
        
        # Return current warning count
        return JsonResponse({'warning_count': attempt.warning_count})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def materials_list(request):
    """List course materials available to the user"""
    user = request.user
    
    if user.is_admin_staff or user.is_staff:
        # Admin can see all materials
        materials = CourseMaterial.objects.all()
    else:
        # Students see only materials for their enrolled batches
        student_batches = get_student_batches(user)
        batch_ids = student_batches.values_list('id', flat=True)
        materials = CourseMaterial.objects.filter(batch__id__in=batch_ids)
    
    materials = materials.order_by('-uploaded_at')
    
    paginator = Paginator(materials, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'materials/list.html', {'page_obj': page_obj})


@login_required
def upload_material(request):
    """Upload course material"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to upload materials.")
    
    if request.method == 'POST':
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user
            material.save()
            messages.success(request, f"Material '{material.title}' uploaded successfully.")
            return redirect('materials_list')
    else:
        form = CourseMaterialForm()
    
    return render(request, 'materials/upload.html', {'form': form})


@login_required
def profile_view(request):
    """View user profile"""
    user = request.user
    
    if hasattr(user, 'student_profile'):
        student_profile = user.student_profile
        batches = student_profile.batches.all()
    else:
        student_profile = None
        batches = []
    
    context = {
        'user': user,
        'profile': student_profile,
        'batches': batches,
    }
    return render(request, 'profile/view.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    user = request.user
    
    if hasattr(user, 'student_profile'):
        student_profile = user.student_profile
    else:
        student_profile = None
        return HttpResponseForbidden("No student profile found.")
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view')
    else:
        form = ProfileUpdateForm(instance=student_profile)
    
    return render(request, 'profile/edit.html', {'form': form})


@login_required
def import_questions(request):
    """Import questions from Excel file"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to import questions.")
    
    if request.method == 'POST':
        form = ImportQuestionsForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Validate columns
                required_columns = ['Question', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Options', 'Marks']
                for column in required_columns:
                    if column not in df.columns:
                        messages.error(request, f"Missing column: {column}")
                        return render(request, 'admin/import_questions.html', {'form': form})
                
                # Process each row
                questions_created = 0
                
                for _, row in df.iterrows():
                    question_text = row['Question']
                    marks = int(row['Marks'])
                    
                    # Parse correct options
                    correct_options = str(row['Correct Options']).split(',')
                    correct_options = [opt.strip() for opt in correct_options]
                    
                    # Create question
                    question = Question.objects.create(
                        text=question_text,
                        marks=marks,
                        multiple_correct=len(correct_options) > 1
                    )
                    
                    # Create options
                    option_mapping = {
                        'A': row['Option A'],
                        'B': row['Option B'],
                        'C': row['Option C'],
                        'D': row['Option D'],
                    }
                    
                    for key, text in option_mapping.items():
                        is_correct = key in correct_options
                        Option.objects.create(
                            question=question,
                            text=text,
                            is_correct=is_correct
                        )
                    
                    questions_created += 1
                
                messages.success(request, f"Successfully imported {questions_created} questions.")
                return redirect('admin_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error importing questions: {str(e)}")
    else:
        form = ImportQuestionsForm()
    
    return render(request, 'admin/import_questions.html', {'form': form})


@login_required
def ai_questions(request):
    """Generate questions using AI from PDF content"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to generate AI questions.")
    
    if request.method == 'POST':
        form = AIQuestionsForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            num_questions = form.cleaned_data['num_questions']
            
            try:
                # Save PDF temporarily
                temp_path = os.path.join('media', 'temp', pdf_file.name)
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, 'wb+') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)
                
                # Generate questions using AI
                questions_data = generate_ai_questions(temp_path, num_questions)
                
                # Create questions in database
                questions_created = 0
                
                for q_data in questions_data:
                    # Create question
                    question = Question.objects.create(
                        text=q_data['question'],
                        marks=q_data['marks'],
                        multiple_correct=len(q_data['correct_options']) > 1
                    )
                    
                    # Create options
                    for i, option_text in enumerate(q_data['options']):
                        is_correct = i in q_data['correct_options']
                        Option.objects.create(
                            question=question,
                            text=option_text,
                            is_correct=is_correct
                        )
                    
                    questions_created += 1
                
                # Clean up temp file
                os.remove(temp_path)
                
                messages.success(request, f"Successfully generated {questions_created} questions using AI.")
                return redirect('admin_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error generating questions: {str(e)}")
    else:
        form = AIQuestionsForm()
    
    return render(request, 'admin/ai_questions.html', {'form': form})


@login_required
def question_list(request):
    """List all questions"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to view all questions.")
    
    questions = Question.objects.all().order_by('-created_at')
    
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/question_list.html', {'questions': page_obj})


@login_required
def create_question(request):
    """Create a new question with options"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create questions.")
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = OptionFormSet(request.POST, prefix='options')
        
        if form.is_valid() and formset.is_valid():
            question = form.save()
            
            # Save options
            for option_form in formset:
                if option_form.cleaned_data.get('text'):
                    option = option_form.save(commit=False)
                    option.question = question
                    # option.is_correct = option_form.cleaned_data.get('is_correct')
                    print("Debugging Options - ",option_form.cleaned_data.get('is_correct'))
                    option.save()
            
            messages.success(request, "Question created successfully.")
            return redirect('question_list')
    else:
        form = QuestionForm()
        formset = OptionFormSet(prefix='options')
    
    return render(request, 'admin/create_question.html', {'form': form, 'formset': formset})


@login_required
def edit_question(request, id):
    """Edit an existing question with options"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to edit questions.")
    
    question = get_object_or_404(Question, id=id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = OptionFormSet(request.POST, instance=question, prefix='options')
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Question updated successfully.")
            return redirect('question_list')
    else:
        form = QuestionForm(instance=question)
        formset = OptionFormSet(instance=question, prefix='options')
    
    return render(request, 'admin/edit_question.html', {'form': form, 'formset': formset, 'question': question})
