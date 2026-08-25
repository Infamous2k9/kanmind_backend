from auth_app.models import User
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
    """CRUD für Boards mit rollenabhängigen Serializern und Permissions."""

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
    """Prüft, ob eine E-Mail-Adresse existiert, und liefert den User zurück."""

    def get(self, request):
        email = request.query_params.get("email")
        user = get_object_or_404(User, email=email)
        serializer = UserShortSerializer(user)
        return Response(serializer.data)


class TaskViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Erstellen, Ändern, Löschen von Tasks (kein Listing laut Doku)."""

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
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data)

    def _check_board_membership(self, board):
        user = self.request.user
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied("You are not a member of this board.")


class AssignedToMeView(generics.ListAPIView):
    """Listet Tasks, bei denen der eingeloggte User Assignee ist."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingView(generics.ListAPIView):
    """Listet Tasks, bei denen der eingeloggte User Reviewer ist."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """Listet Kommentare einer Task und erstellt neue Kommentare."""

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
    """Löscht einen Kommentar – nur der Autor darf das."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]  # noqa: RUF012
    lookup_url_kwarg = "comment_id"
