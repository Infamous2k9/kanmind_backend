from auth_app.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Board, Comment, Task

from .permissions import (
    IsBoardMember,
    IsBoardOwner,
    IsCommentAuthor,
    IsTaskBoardMember,
    IsTaskCreatorOrBoardOwner,
)
from .serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    TaskCreateUpdateSerializer,
    TaskSerializer,
    UserShortSerializer,
)


class BoardViewSet(viewsets.ModelViewSet):
    """CRUD for boards with role-dependent serializers and permissions."""

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return BoardListSerializer
        if self.action == "create":
            return BoardCreateSerializer
        if self.action in ("update", "partial_update"):
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsBoardOwner()]
        if self.action in ("retrieve", "update", "partial_update"):
            return [permissions.IsAuthenticated(), IsBoardMember()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save()
        output = BoardListSerializer(board)
        return Response(output.data, status=status.HTTP_201_CREATED)


class EmailCheckView(APIView):
    """Checks if an email address exists and returns the user."""

    def get(self, request):
        email = request.query_params.get("email")
        error = self._validate_email_param(email)
        if error:
            return Response({"email": error}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, email=email)
        return Response(UserShortSerializer(user).data)

    def _validate_email_param(self, email):
        if not email:
            return "This query parameter is required."
        try:
            validate_email(email)
        except ValidationError:
            return "Invalid email format."
        return None


class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Create, update, delete tasks (no listing according to documentation)."""

    queryset = Task.objects.all()
    serializer_class = TaskCreateUpdateSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return [permissions.IsAuthenticated(), IsTaskBoardMember()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._check_board_membership(serializer.validated_data["board"])
        task = serializer.save(created_by=request.user)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if "board" in request.data and int(request.data["board"]) != instance.board_id:
            return Response(
                {"board": "Board cannot be changed after creation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data)

    def _check_board_membership(self, board):
        user = self.request.user
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("You are not a member of this board.")


class AssignedToMeView(generics.ListAPIView):
    """Lists tasks where the logged-in user is the assignee."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingView(generics.ListAPIView):
    """Lists tasks where the logged-in user is the reviewer."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """Lists comments for a task and creates new comments."""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]  # noqa: RUF012

    def get_task(self):
        task = get_object_or_404(Task, pk=self.kwargs["task_id"])
        self.check_object_permissions(self.request, task)
        return task

    def get_queryset(self):
        return self.get_task().comments.all()

    def perform_create(self, serializer):
        serializer.save(task=self.get_task(), author=self.request.user)


class CommentDeleteView(generics.DestroyAPIView):
    """Deletes a comment – only the author is allowed to do so."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]  # noqa: RUF012
    lookup_url_kwarg = "comment_id"
