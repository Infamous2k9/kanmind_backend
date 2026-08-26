from rest_framework import permissions


class IsBoardMember(permissions.BasePermission):
    """Grants access only to board members or the board owner."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner or request.user in obj.members.all()


class IsBoardOwner(permissions.BasePermission):
    """Grants access only to the board owner (e.g., for deletion)."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class IsTaskBoardMember(permissions.BasePermission):
    """Grants access only to members/owner of the board to which the task belongs."""

    def has_object_permission(self, request, view, obj):
        board = obj.board
        return request.user == board.owner or request.user in board.members.all()


class IsTaskCreatorOrBoardOwner(permissions.BasePermission):
    """Grants permission to delete a task only to the creator or the board owner."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.created_by or request.user == obj.board.owner


class IsCommentAuthor(permissions.BasePermission):
    """Grants permission to delete a comment only to the author."""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.author
