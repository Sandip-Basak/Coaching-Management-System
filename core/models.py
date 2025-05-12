import uuid
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Extended user model"""
    is_student = models.BooleanField(default=True)
    is_admin_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class StudentProfile(models.Model):
    """Student profile extending the User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    approved = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    device_identifier = models.CharField(max_length=255, null=True, blank=True)
    session_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class Course(models.Model):
    """Course model"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Batch(models.Model):
    """Batch model"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='batches')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    students = models.ManyToManyField(StudentProfile, related_name='batches', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"


class Question(models.Model):
    """Question model"""
    text = models.TextField()
    marks = models.IntegerField(default=1)
    multiple_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Question: {self.text[:50]}..."


class Option(models.Model):
    """Option model for a question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.text} - {'Correct' if self.is_correct else 'Incorrect'}"


class PracticePaper(models.Model):
    """Practice paper model"""
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='practice_papers')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_practice_papers')
    allowed_for_trial = models.BooleanField(default=False)
    trial_question_count = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    time_limit = models.IntegerField(help_text="Time limit in minutes")
    questions = models.ManyToManyField(Question, related_name='practice_papers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"


class MockExam(models.Model):
    """Mock exam model"""
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='mock_exams')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_mock_exams')
    time_limit = models.IntegerField(help_text="Time limit in minutes")
    questions = models.ManyToManyField(Question, related_name='mock_exams')
    results_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"


class Attempt(models.Model):
    """Attempt model for practice papers and mock exams"""
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    TYPE_CHOICES = (
        ('practice', 'Practice Paper'),
        ('mock', 'Mock Exam'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    # Track what kind of paper is being attempted
    attempt_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    practice_paper = models.ForeignKey(PracticePaper, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    mock_exam = models.ForeignKey(MockExam, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress')
    score = models.FloatField(null=True, blank=True)
    is_trial = models.BooleanField(default=False)
    warning_count = models.IntegerField(default=0)
    
    def __str__(self):
        user_str = self.user.username if self.user else "Trial User"
        if self.attempt_type == 'practice':
            paper_name = self.practice_paper.name
        else:
            paper_name = self.mock_exam.name
        return f"{user_str} - {paper_name} - {self.status}"


class Answer(models.Model):
    """Model to store answers for an attempt"""
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option, related_name='selected_answers')
    
    def __str__(self):
        return f"Answer for {self.question} in {self.attempt}"


class CourseMaterial(models.Model):
    """Course materials model"""
    TYPE_CHOICES = (
        ('pdf', 'PDF Document'),
        ('video', 'Video Link'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    material_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='course_materials/', null=True, blank=True)
    video_embed_code = models.TextField(null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='materials')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_materials')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.batch.name}"
