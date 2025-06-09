from django.contrib.auth.models import User
from django.db import models

class Board(models.Model):
    title = models.CharField(max_length=255)
    create_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class List(models.Model):
    board = models.ForeignKey(Board, related_name='lists', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title


class Status(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Statuses"

def get_default_status():
    return Status.objects.get(name="Не начата").id

class Task(models.Model):
    list = models.ForeignKey(List, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, default=get_default_status())
    dateStarted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TaskFile(models.Model):
    task = models.ForeignKey(Task, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='task_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)