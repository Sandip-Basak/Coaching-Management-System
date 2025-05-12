from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import inlineformset_factory
from .models import (
    User, StudentProfile, Course, Batch, Question, Option,
    PracticePaper, MockExam, CourseMaterial
)


class SignUpForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    profile_photo = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_student = True
        
        if commit:
            user.save()
        
        return user


class LoginForm(AuthenticationForm):
    """Form for user login"""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating student profile"""
    class Meta:
        model = StudentProfile
        fields = ('profile_photo',)


class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    class Meta:
        model = Course
        fields = ('name', 'description', 'slug')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'slug': 'URL-friendly name (e.g., "python-programming"). Leave blank to auto-generate.',
        }


class BatchForm(forms.ModelForm):
    """Form for creating/editing batches"""
    class Meta:
        model = Batch
        fields = ('course', 'name', 'start_date', 'end_date', 'students')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class QuestionForm(forms.ModelForm):
    """Form for creating/editing questions"""
    class Meta:
        model = Question
        fields = ('text', 'marks', 'multiple_correct')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


OptionFormSet = inlineformset_factory(
    Question, Option, 
    fields=('text', 'is_correct'),
    extra=4, can_delete=True,
    widgets={'text': forms.TextInput(attrs={'class': 'form-control'})}
)


class PracticePaperForm(forms.ModelForm):
    """Form for creating/editing practice papers"""
    class Meta:
        model = PracticePaper
        fields = ('name', 'course', 'allowed_for_trial', 'trial_question_count', 'time_limit', 'questions')
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 5, 'max': 180}),
            'trial_question_count': forms.NumberInput(attrs={'min': 1, 'max': 20}),
        }
        help_texts = {
            'time_limit': 'Time limit in minutes',
            'trial_question_count': 'Number of random questions for trial users (1-20)',
        }


class MockExamForm(forms.ModelForm):
    """Form for creating/editing mock exams"""
    class Meta:
        model = MockExam
        fields = ('name', 'course', 'time_limit', 'questions', 'results_released')
        widgets = {
            'time_limit': forms.NumberInput(attrs={'min': 5, 'max': 180}),
        }
        help_texts = {
            'time_limit': 'Time limit in minutes',
            'results_released': 'Check to make results visible to students',
        }


class ImportQuestionsForm(forms.Form):
    """Form for importing questions from Excel"""
    excel_file = forms.FileField(
        label='Select Excel File',
        help_text='Excel file must have columns: Question, Option A-D, Correct Options (comma-separated), Marks'
    )


class AIQuestionsForm(forms.Form):
    """Form for generating questions using AI from PDF"""
    pdf_file = forms.FileField(label='Upload PDF')
    num_questions = forms.IntegerField(
        label='Number of Questions', 
        min_value=1, 
        max_value=50,
        initial=10,
        help_text='How many questions to generate (1-50)'
    )


class CourseMaterialForm(forms.ModelForm):
    """Form for uploading course materials"""
    class Meta:
        model = CourseMaterial
        fields = ('title', 'description', 'material_type', 'file', 'video_embed_code', 'batch')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'video_embed_code': forms.Textarea(attrs={'rows': 3}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        material_type = cleaned_data.get('material_type')
        file = cleaned_data.get('file')
        video_embed_code = cleaned_data.get('video_embed_code')
        
        if material_type == 'pdf' and not file:
            self.add_error('file', 'PDF file is required for this material type.')
        
        if material_type == 'video' and not video_embed_code:
            self.add_error('video_embed_code', 'Video embed code is required for this material type.')
        
        return cleaned_data
