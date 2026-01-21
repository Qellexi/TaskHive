from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class OrganizationManager(models.Manager):
    def for_user(self, user):
        return self.filter(organization=user.organization)


class WorkerManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Creates and saves a regular user with the given username, email, password.
        """
        if not username:
            raise ValueError("The Username must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        if "organization" not in extra_fields or extra_fields["organization"] is None:
            default_organization, _ = Organization.objects.get_or_create(
                name="Default Organization",
            )
            extra_fields["organization"] = default_organization

        return self.create_user(username, email, password, **extra_fields)


class Worker(AbstractUser):
    first_name = models.CharField(
        max_length=30,
        verbose_name=_("First Name")
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name=_("Last Name")
    )
    position = models.ForeignKey(
        "Position",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=100,
        verbose_name=_("Role"),
        default="member",
    )
    objects = WorkerManager()
    class Meta:
        ordering = ["username",]

    def get_absolute_url(self):
        return reverse("management:worker-detail", kwargs={"pk": self.pk})


    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class TaskType(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(
        max_length=7,
        default="#ffd6d1"
    )

    def __str__(self):
        return self.name

class Task(models.Model):
    class Priority(models.TextChoices):
        urgent = "urgent", _("urgent")
        medium = "medium", _("medium")
        low = "low", _("low")

    class Status(models.TextChoices):
        todo = "todo", _("todo")
        in_progress = "in_progress", _("in_progress")
        done = "done", _("done")

    name = models.CharField(max_length=100)
    description = models.TextField()
    is_completed = models.BooleanField(default=False)
    type = ForeignKey(TaskType, on_delete=models.PROTECT)
    workers = models.ManyToManyField("Worker", related_name="tasks")
    project = models.ForeignKey("Project", on_delete=models.PROTECT)
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.urgent,
    )
    status = models.CharField(
        max_length=100,
        choices=Status.choices,
        default=Status.todo
    )
    deadline = models.DateTimeField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["project", "priority", "name",]

    def get_absolute_url(self):
        return reverse("management:task-detail", kwargs={"pk": self.pk})



class Department(models.Model):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class Position(models.Model):
    name = models.CharField(
        max_length=100,
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="positions",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["department", "name",]

    def __str__(self):
        return f"{self.name} ({self.department.name} department)"

class Team(models.Model):
    name = models.CharField(max_length=100)
    workers = models.ManyToManyField("Worker", related_name="teams")

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name",]

    def get_absolute_url(self):
        return reverse("management:team-detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name}: ({self.workers.count()} workers)"

class Project(models.Model):
    name = models.CharField(max_length=100)
    teams = models.ManyToManyField("Team", related_name="projects")
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse("management:project-detail", kwargs={"pk": self.pk})

    def __str__(self):
        team_names = ", ".join(team.name for team in self.teams.all())
        return f"{self.name} - ({team_names})"


class Comment(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.PROTECT)
    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        pass

    def __str__(self):
        return f"{self.worker} left comment on task ({self.task}): {self.text}"


def get_default_room_name():
    return f"Group {ChatRoom.objects.count() + 1}"


class ChatRoom(models.Model):
    name = models.CharField(
        max_length=100,
        default=get_default_room_name,
        blank=True,
        null=True,
    )
    members = models.ManyToManyField(Worker, related_name="chat_rooms")
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def is_private(self):
        return self.name.startswith("private_")

    def other_member(self, current_worker):
        """excludes the other person in private chat"""
        return self.members.exclude(id=current_worker.id).first()


class Message(models.Model):
    sender = models.ForeignKey(Worker, on_delete=models.CASCADE)
    content = models.TextField()
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="chats")
    timestamp = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.sender} -> {self.content}"


class Feedback(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.name}: {self.email}"