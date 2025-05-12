from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import User, StudentProfile, Answer, Attempt
from django.utils import timezone


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """Create a StudentProfile for each new User with is_student=True"""
    if created and instance.is_student:
        StudentProfile.objects.create(user=instance)


@receiver(post_save, sender=Answer)
def update_attempt_score_on_answer(sender, instance, created, **kwargs):
    """Update the attempt score whenever an answer is saved"""
    # m2m_changed will handle this when selected_options are changed


@receiver(m2m_changed, sender=Answer.selected_options.through)
def update_attempt_score_on_options_change(sender, instance, action, **kwargs):
    """Update the attempt score when selected options change"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        attempt = instance.attempt
        
        # Only update completed attempts
        if attempt.status == 'completed':
            from .utils import calculate_score
            
            attempt.score = calculate_score(attempt)
            attempt.save(update_fields=['score'])


@receiver(post_save, sender=Attempt)
def handle_attempt_completion(sender, instance, **kwargs):
    """Handle attempt when status changes to completed"""
    if instance.status == 'completed' and not instance.end_time:
        # Set end time if not already set
        instance.end_time = timezone.now()
        
        # Calculate score
        from .utils import calculate_score
        instance.score = calculate_score(instance)
        
        # Save without triggering this signal again
        Attempt.objects.filter(id=instance.id).update(
            end_time=instance.end_time,
            score=instance.score
        )
