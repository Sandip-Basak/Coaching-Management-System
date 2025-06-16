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
        widgets = {
            'profile_photo' : forms.FileInput(attrs={'class': 'form-control'}),
        }


class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    class Meta:
        model = Course
        fields = ('name', 'description', 'slug')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
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
            'course': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control bg-dark'}),
        }


class QuestionForm(forms.ModelForm):
    """Form for creating/editing questions"""
    class Meta:
        model = Question
        fields = ('course', 'text', 'marks', 'multiple_correct')
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'text': forms.Textarea(attrs={'rows': 3,'class': 'form-control'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'multiple_correct' : forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }


OptionFormSet = inlineformset_factory(
    Question, Option, 
    fields=('text', 'is_correct'),
    extra=4, can_delete=True,
    widgets={'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct' : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
}
)


class PracticePaperForm(forms.ModelForm):
    """Form for creating/editing practice papers"""
    class Meta:
        model = PracticePaper
        fields = ('name', 'course', 'allowed_for_trial', 'trial_question_count', 'time_limit', 'questions')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'allowed_for_trial' : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'time_limit': forms.NumberInput(attrs={'min': 5, 'max': 180, 'class': 'form-control bg-dark'}),
            'trial_question_count': forms.NumberInput(attrs={'min': 1, 'max': 20, 'class': 'form-control bg-dark'}),
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
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'time_limit': forms.NumberInput(attrs={'min': 5, 'max': 180, 'class': 'form-control'}),
            'results_released' : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'time_limit': 'Time limit in minutes',
            'results_released': 'Check to make results visible to students',
        }


class ImportQuestionsForm(forms.Form):
    """Form for importing questions from Excel"""
    excel_file = forms.FileField(
        label='Select Excel File',
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Excel file must have columns: Question, Option A-D, Correct Options (comma-separated), Marks'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(), # Allow selecting any existing course
        label='Select Course',
        empty_label='--- Select a Course ---',
        widget=forms.Select(attrs={'class': 'form-control bg-dark'}),
    )


class AIQuestionsForm(forms.Form):
    """Form for generating questions using AI from PDF"""
    pdf_file = forms.FileField(label='Upload PDF',widget=forms.FileInput(attrs={'class': 'form-control'}))
    num_questions = forms.IntegerField(
        label='Number of Questions', 
        min_value=1, 
        max_value=50,
        initial=10,
        help_text='How many questions to generate (1-50)',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(), # Allow selecting any existing course
        label='Select Course',
        empty_label='--- Select a Course ---',
        widget=forms.Select(attrs={'class': 'form-control bg-dark'}),
    )


class CourseMaterialForm(forms.ModelForm):
    """Form for uploading course materials"""
    class Meta:
        model = CourseMaterial
        fields = ('title', 'description', 'material_type', 'file', 'video_embed_code','external_url' , 'batch')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3,'class': 'form-control'}),
            'material_type': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'video_embed_code': forms.Textarea(attrs={'rows': 3,'class': 'form-control'}),
            'file' : forms.FileInput(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control bg-dark'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        material_type = cleaned_data.get('material_type')
        file = cleaned_data.get('file')
        video_embed_code = cleaned_data.get('video_embed_code')
        external_url = cleaned_data.get('external_url')
        
        if material_type == 'pdf' and not file:
            self.add_error('file', 'PDF file is required for this material type.')
        
        if material_type == 'video' and not video_embed_code:
            self.add_error('video_embed_code', 'Video embed code is required for this material type.')
        
        if material_type == 'link' and not external_url:
            self.add_error('external_url', 'External URL is required for this material type.')

        return cleaned_data
