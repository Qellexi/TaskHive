from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from management.forms import (
    WorkerRegistrationForm, OrganizationForm, ProjectForm,
    ChatGroupForm, TaskForm, TeamForm, CommentForm, FeedbackForm
)
from management.models import (
    Worker, Organization, Project, ChatRoom, Task,
    TaskType, Team, Comment, Feedback
)

User = get_user_model()
# ---------------------------------------------------------------------
# Worker Registration Form
# ---------------------------------------------------------------------
class WorkerRegistrationFormTests(TestCase):

    def test_registration_form_valid(self):
        org = Organization.objects.create(name="Org")

        form = WorkerRegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johnny",
            "email": "john@example.com",
            "password": "12345",
            "organization": org.id
        })

        self.assertTrue(form.is_valid())

    def test_registration_form_missing_org(self):
        form = WorkerRegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johnny",
            "email": "john@example.com",
            "password": "12345",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("organization", form.errors)


# ---------------------------------------------------------------------
# Organization Form
# ---------------------------------------------------------------------
class OrganizationFormTests(TestCase):

    def test_create_new_organization(self):
        form = OrganizationForm(data={
            "name": "",
            "code": "",
            "existing_organization": "",
        })

        self.assertTrue(form.is_valid())
        org = form.save()

        self.assertTrue(org.name.startswith("Organization"))
        self.assertIsNotNone(org.code)

    def test_use_existing_organization(self):
        existing = Organization.objects.create(name="OldOrg", code="123ABC")

        form = OrganizationForm(data={
            "existing_organization": existing.id,
            "name": "",
            "code": ""
        })

        self.assertTrue(form.is_valid())
        result = form.save()

        self.assertEqual(result, existing)


# ---------------------------------------------------------------------
# Project Form
# ---------------------------------------------------------------------
class ProjectFormTests(TestCase):

    def test_project_form_valid(self):
        org = Organization.objects.create(name="Test Org")
        team1 = Team.objects.create(name="Test Team1", organization=org)
        team2 = Team.objects.create(name="Test Team2", organization=org)
        form = ProjectForm(data={
            "name": "Proj1",
            "deadline": "2025-01-01",
            "description": "",
            "teams": [team1.id, team2.id],
        })

        self.assertTrue(form.is_valid())


# ---------------------------------------------------------------------
# ChatGroup Form
# ---------------------------------------------------------------------
class ChatGroupFormTests(TestCase):

    def test_chat_group_form_valid(self):
        form = ChatGroupForm(data={"name": "Group A"})

        self.assertTrue(form.is_valid())


# ---------------------------------------------------------------------
# Task Form
# ---------------------------------------------------------------------
class TaskFormTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.project = Project.objects.create(name="P1", organization=self.org)
        self.type = TaskType.objects.create(name="Bug", color="#ffd6d1")
        self.worker = User.objects.create_user(
            "test_user", "user@test.com", "12345",
            organization=self.org
        )

    def test_task_form_requires_type_if_not_creating_new(self):
        form = TaskForm(data={
            "name": "Task1",
            "description": "Desc",
            "is_completed": False,
            "create_new_type": False,
            "type": "",
            "priority": "urgent",
            "status": "todo",
            "workers": self.worker.id,
            "project": self.project.id,
            "deadline": "2025-01-01",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("type", form.errors)

    def test_task_form_requires_new_type_name_if_creating(self):
        form = TaskForm(data={
            "name": "Task1",
            "description": "Desc",
            "create_new_type": True,
            "new_type_name": "",
            "new_type_color": "#ffd6d1",
            "priority": "urgent",
            "status": "todo",
            "project": self.project.id,
            "deadline": "2025-01-01",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("new_type_name", form.errors)

    def test_task_form_creates_new_type(self):
        form = TaskForm(data={
            "name": "Task1",
            "description": "Desc",
            "create_new_type": True,
            "new_type_name": "NewType",
            "new_type_color": "#fafaa3",
            "priority": "urgent",
            "status": "todo",
            "project": self.project.id,
            "deadline": "2025-01-01",
        })

        self.assertTrue(form.is_valid())
        task = form.save()

        self.assertEqual(task.type.name, "NewType")

    def test_task_form_uses_existing_type(self):
        form = TaskForm(data={
            "name": "Task1",
            "description": "Desc",
            "create_new_type": False,
            "type": self.type.id,
            "priority": "urgent",
            "status": "todo",
            "project": self.project.id,
            "deadline": "2025-01-01",
        })

        self.assertTrue(form.is_valid())
        task = form.save()

        self.assertEqual(task.type, self.type)

# ---------------------------------------------------------------------
# Team Form
# ---------------------------------------------------------------------
class TeamFormTests(TestCase):

    def test_team_form_valid(self):
        form = TeamForm(data={
            "name": "Team1",
        })
        self.assertTrue(form.is_valid())

# ---------------------------------------------------------------------
# Comment Form
# ---------------------------------------------------------------------
class CommentFormTests(TestCase):

    def test_comment_form_valid(self):
        form = CommentForm(data={"text": "Hello world"})
        self.assertTrue(form.is_valid())

# ---------------------------------------------------------------------
# Feedback Form
# ---------------------------------------------------------------------
class FeedbackFormTests(TestCase):

    def test_feedback_form_valid(self):
        form = FeedbackForm(data={
            "name": "John",
            "email": "john@mail.com",
            "message": "Hi!"
        })

        self.assertTrue(form.is_valid())