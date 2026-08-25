from rest_framework import permissions


class IsBoardMember(permissions.BasePermission):
    """Erlaubt Zugriff nur Mitgliedern oder dem Owner des Boards."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner or request.user in obj.members.all()


class IsBoardOwner(permissions.BasePermission):
    """Erlaubt Zugriff nur dem Owner des Boards (z. B. zum Löschen)."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class IsTaskBoardMember(permissions.BasePermission):
    """Erlaubt Zugriff nur Mitgliedern/Owner des Boards, zu dem die Task gehört."""

    def has_object_permission(self, request, view, obj):
        board = obj.board
        return request.user == board.owner or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """Erlaubt das Löschen einer Task nur dem Ersteller oder dem Board-Owner."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.created_by or request.user == obj.board.owner


class IsCommentAuthor(permissions.BasePermission):
    """Erlaubt das Löschen eines Kommentars nur dem Autor."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.author
