from django.contrib import admin

from .models import Board, Comment, Task

admin.site.register(Board)
admin.site.register(Task)
admin.site.register(Comment)
