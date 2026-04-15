import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import VideoFile

@receiver(post_delete, sender=VideoFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Удаляет физический файл с диска при удалении объекта VideoFile.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)