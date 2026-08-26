from auth_app.models import User
from rest_framework import serializers

from kanban_app.models import Board, Comment, Task


class UserShortSerializer(serializers.ModelSerializer):
    """Compact user representation for nested responses."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]  # noqa: RUF012


# ---------- Board ----------


class BoardListSerializer(serializers.ModelSerializer):
    """For GET/POST /boards/ - flat fields with computed counts."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [  # noqa: RUF012
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()


class BoardCreateSerializer(serializers.ModelSerializer):
    """For POST /boards/ – takes title + member IDs."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Board
        fields = ["id", "title", "members"]  # noqa: RUF012

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        board = Board.objects.create(
            owner=self.context["request"].user, **validated_data
        )
        board.members.set(members)
        return board


class TaskShortSerializer(serializers.ModelSerializer):
    """Task representation nested inside the board detail view."""

    assignee = UserShortSerializer(read_only=True)
    reviewer = UserShortSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [  # noqa: RUF012
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """FFor GET /boards/{id}/ – with full member and task objects."""

    members = UserShortSerializer(many=True, read_only=True)
    tasks = TaskShortSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]  # noqa: RUF012


class BoardUpdateSerializer(serializers.ModelSerializer):
    """For PATCH /boards/{id}/ - response includes owner_data/members_data."""

    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    owner_data = UserShortSerializer(source="owner", read_only=True)
    members_data = UserShortSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]  # noqa: RUF012

    def update(self, instance, validated_data):
        members = validated_data.pop("members", None)
        instance.title = validated_data.get("title", instance.title)
        instance.save()
        if members is not None:
            instance.members.set(members)
        return instance


# ---------- Task ----------


class TaskSerializer(serializers.ModelSerializer):
    """Read serializer for tasks - nested assignee/reviewer objects."""

    assignee = UserShortSerializer(read_only=True)
    reviewer = UserShortSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [  # noqa: RUF012
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Write serializer for tasks - accepts assignee_id/reviewer_id."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee", queryset=User.objects.all(), required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer", queryset=User.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [  # noqa: RUF012
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]

    def validate(self, attrs):
        board = self.instance.board if self.instance else attrs.get("board")
        for field in ("assignee", "reviewer"):
            user = attrs.get(field)
            if (
                user
                and not board.members.filter(id=user.id).exists()
                and user != board.owner
            ):
                raise serializers.ValidationError(
                    f"{field} must be a member of the board."
                )
        return attrs


# ---------- Comment ----------


class CommentSerializer(serializers.ModelSerializer):
    """Comment response with author represented as a plain name string."""

    author = serializers.CharField(source="author.fullname", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]  # noqa: RUF012
