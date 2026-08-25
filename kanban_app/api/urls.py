from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssignedToMeView,
    BoardViewSet,
    CommentDeleteView,
    CommentListCreateView,
    EmailCheckView,
    ReviewingView,
    TaskViewSet,
)

router = DefaultRouter()
router.register("boards", BoardViewSet, basename="board")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path(
        "tasks/assigned-to-me/", AssignedToMeView.as_view(), name="tasks-assigned-to-me"
    ),
    path("tasks/reviewing/", ReviewingView.as_view(), name="tasks-reviewing"),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        CommentDeleteView.as_view(),
        name="task-comment-delete",
    ),
] + router.urls
