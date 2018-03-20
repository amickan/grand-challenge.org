from django.db.models.signals import post_save
from django.dispatch import receiver

from participants.models import RegistrationRequest


@receiver(post_save, sender=RegistrationRequest)
def process_registration(
    instance: RegistrationRequest = None, created: bool = False, *_, **__
):
    if created and not instance.challenge.require_participant_review:
        instance.status = RegistrationRequest.ACCEPTED
        RegistrationRequest.objects.filter(pk=instance.pk).update(
            status=instance.status
        )
    if instance.status == RegistrationRequest.ACCEPTED:
        instance.challenge.add_participant(instance.user)
    else:
        instance.challenge.remove_participant(instance.user)
