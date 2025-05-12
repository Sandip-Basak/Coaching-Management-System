import os
import json
import uuid
import base64
import requests
from django.conf import settings
from django.utils import timezone
from PyPDF2 import PdfReader


def get_student_batches(user):
    """Get batches for a student user"""
    if hasattr(user, 'student_profile'):
        return user.student_profile.batches.all()
    return []


def calculate_score(attempt):
    """Calculate score for an attempt"""
    total_score = 0
    total_possible = 0
    
    for answer in attempt.answers.all():
        question = answer.question
        selected_options = answer.selected_options.all()
        correct_options = question.options.filter(is_correct=True)
        
        total_possible += question.marks
        
        if question.multiple_correct:
            # All correct options must be selected and no incorrect ones
            selected_correct = set(opt.id for opt in selected_options if opt.is_correct)
            all_correct = set(opt.id for opt in correct_options)
            selected_incorrect = any(not opt.is_correct for opt in selected_options)
            
            if selected_correct == all_correct and not selected_incorrect:
                total_score += question.marks
        else:
            # Single correct answer
            if len(selected_options) == 1 and selected_options.first().is_correct:
                total_score += question.marks
    
    # Calculate percentage if possible
    if total_possible > 0:
        score_percentage = (total_score / total_possible) * 100
    else:
        score_percentage = 0
    
    return score_percentage


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def generate_ai_questions(pdf_path, num_questions):
    """Generate questions using Google Gemini API from PDF content"""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("Gemini API key not configured")
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_path)
    
    # Limit text length to avoid token limits
    max_chars = 10000
    if len(pdf_text) > max_chars:
        pdf_text = pdf_text[:max_chars]
    
    # Create prompt for Gemini
    prompt = f"""
    Generate {num_questions} multiple-choice questions (MCQs) based on the following content.
    
    Content:
    {pdf_text}
    
    Return the questions in JSON format:
    [
      {{
        "question": "Clear, concise question text",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_options": [0, 1],  // Zero-based indices of correct options (can be multiple)
        "marks": 2  // Points for this question (between 1-5)
      }},
      // more questions...
    ]
    
    Ensure each question:
    1. Is clear and directly related to the content
    2. Has exactly 4 options
    3. Has at least one correct answer (could have multiple)
    4. Has appropriate marks (1-5 based on difficulty)
    5. Use zero-based array indices for correct_options
    """
    
    # Make request to Gemini API
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        }
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    # Parse the response
    result = response.json()
    
    try:
        generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Extract JSON part from response
        start_idx = generated_text.find('[')
        end_idx = generated_text.rfind(']') + 1
        json_text = generated_text[start_idx:end_idx]
        
        # Parse JSON
        questions_data = json.loads(json_text)
        return questions_data
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        raise Exception(f"Failed to parse API response: {str(e)}")


def get_active_course_count():
    """Get count of active courses for dashboard stats"""
    from .models import Course
    return Course.objects.count()


def get_active_student_count():
    """Get count of approved students for dashboard stats"""
    from .models import StudentProfile
    return StudentProfile.objects.filter(approved=True).count()


def get_pending_approval_count():
    """Get count of students pending approval for dashboard stats"""
    from .models import StudentProfile
    return StudentProfile.objects.filter(approved=False).count()
