from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Attempt, Question, Option, Answer
from django.shortcuts import get_object_or_404
from django.utils import timezone


@login_required
@require_POST
def save_answer(request):
    """API endpoint to save an answer during exam"""
    attempt_id = request.POST.get('attempt_id')
    question_id = request.POST.get('question_id')
    option_ids = request.POST.getlist('option_ids[]')
    
    attempt = get_object_or_404(Attempt, id=attempt_id)
    
    # Check if the attempt belongs to the user
    if attempt.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Check if the attempt is still in progress
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'This attempt is no longer in progress'}, status=400)
    
    question = get_object_or_404(Question, id=question_id)
    
    # Remove any existing answer for this question
    Answer.objects.filter(attempt=attempt, question=question).delete()
    
    # Create new answer
    answer = Answer.objects.create(
        attempt=attempt,
        question=question
    )
    
    # Add selected options
    for option_id in option_ids:
        option = get_object_or_404(Option, id=option_id)
        if option.question.id != question.id:
            return JsonResponse({'error': 'Option does not belong to this question'}, status=400)
        answer.selected_options.add(option)
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def extend_time(request):
    """API endpoint to extend time for an attempt (admin only)"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    attempt_id = request.POST.get('attempt_id')
    additional_minutes = request.POST.get('additional_minutes', 10)
    try:
        additional_minutes = int(additional_minutes)
    except ValueError:
        additional_minutes = 10
    
    attempt = get_object_or_404(Attempt, id=attempt_id)
    
    # Only extend if the attempt is still in progress
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'This attempt is no longer in progress'}, status=400)
    
    # Calculate new end time
    if attempt.end_time:
        new_end_time = attempt.end_time + timezone.timedelta(minutes=additional_minutes)
    else:
        # If end_time is not set, use current time + time limit + additional minutes
        if attempt.attempt_type == 'practice':
            time_limit = attempt.practice_paper.time_limit
        else:
            time_limit = attempt.mock_exam.time_limit
        new_end_time = attempt.start_time + timezone.timedelta(minutes=time_limit + additional_minutes)
    
    attempt.end_time = new_end_time
    attempt.save()
    
    return JsonResponse({
        'success': True,
        'new_end_time': new_end_time.isoformat()
    })


@login_required
@require_POST
def reset_warnings(request):
    """API endpoint to reset warnings for an attempt (admin only)"""
    if not request.user.is_admin_staff and not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    attempt_id = request.POST.get('attempt_id')
    attempt = get_object_or_404(Attempt, id=attempt_id)
    
    # Only reset if the attempt is still in progress
    if attempt.status != 'in_progress':
        return JsonResponse({'error': 'This attempt is no longer in progress'}, status=400)
    
    attempt.warning_count = 0
    attempt.save()
    
    return JsonResponse({'success': True})
