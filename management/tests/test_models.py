from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from management.models import Organization, TaskType, Department, Position, Team, Project, Task, Comment, ChatRoom, \
    Message, Feedback

User = get_user_model()

class ModelTests(TestCase):
    def test_organization_str(self):
        org = Organization.objects.create(name="Test Org")
        self.assertEqual(str(org), "Test Org")

    def test_worker_manager_create_user(self):
        org = Organization.objects.create(name="Test Org")
        user = User.objects.create_user(
            username="test_user",
            email="user@test.com",
            password="12345",
            organization=org
        )
        self.assertEqual(user.username, "test_user")
        self.assertTrue(user.check_password("12345"))

    def test_worker_str(self):
        org = Organization.objects.create(name="Test Org")
        worker = User.objects.create_user(
            "test_user", "user@test.com", "12345",
            first_name="John", last_name="Doe",
            organization=org
        )
        self.assertEqual(str(worker), "John Doe (user@test.com)")

    def test_worker_get_absolute_url(self):
        org = Organization.objects.create(name="Test Org")
        worker = User.objects.create_user(
            "test_user", "user@test.com", "12345",
            organization=org
        )
        self.assertEqual(
            worker.get_absolute_url(),
            reverse("management:worker-detail", kwargs={"pk": worker.pk})
        )

    def task_type_str(self):
        tt = TaskType.objects.create(name="Bug")
        self.assertEqual(str(tt), "Bug")

    def test_department_position_str(self):
        org = Organization.objects.create(name="Test Org")
        dept = Department.objects.create(name="Test Department")
        pos = Position.objects.create(name="Dev", department=dept, organization=org)
        self.assertEqual(str(pos), "Dev (Test Department department)")

    def test_team_str(self):
        org = Organization.objects.create(name="Test Org")
        team = Team.objects.create(name="Test Team", organization=org)
        self.assertEqual(
            team.get_absolute_url(),
            reverse("management:team-detail", kwargs={"pk": team.pk})
        )

    def test_project_str(self):
        org = Organization.objects.create(name="Test Org")
        team = Team.objects.create(name="Test Team", organization=org)
        project = Project.objects.create(name="Test Project", organization=org)
        project.teams.add(team)
        self.assertEqual(
            str(project), "Test Project - (Test Team)"
        )

    def test_project_get_absolute_url(self):
        org = Organization.objects.create(name="Test Org")
        project = Project.objects.create(name="Test Project", organization=org)
        self.assertEqual(
            project.get_absolute_url(),
            reverse("management:project-detail", kwargs={"pk": project.pk})
        )

    def test_task_creation(self):
        org = Organization.objects.create(name="Test Org")
        project = Project.objects.create(name="Test Project", organization=org)
        tt = TaskType.objects.create(name="Bug")
        team = Team.objects.create(name="Test Team", organization=org)
        project.teams.add(team)
        worker = User.objects.create_user(
            "john", "j@gmail.com", "123", organization=org
        )

        task = Task.objects.create(
            name="Fix bug",
            description="Details...",
            type=tt,
            project=project,
            priority="urgent",
            status="todo",
            organization=org,
        )
        task.workers.add(worker)
        self.assertEqual(task.name, "Fix bug")
        self.assertIn(worker, task.workers.all())

    def test_task_get_absolute_url(self):
        org = Organization.objects.create(name="Test Org")
        tt = TaskType.objects.create(name="Bug")
        project = Project.objects.create(name="Test Project", organization=org)

        task = Task.objects.create(
            name="Task",
            description="",
            type=tt,
            project=project,
            organization=org,
        )
        self.assertEqual(
            task.get_absolute_url(),
            reverse("management:task-detail", kwargs={"pk": task.pk})
        )

    def test_comment_str(self):
        org = Organization.objects.create(name="Org")
        tt = TaskType.objects.create(name="Bug")
        proj = Project.objects.create(name="P1", organization=org)
        task = Task.objects.create(name="Bug", description="d", type=tt, project=proj, organization=org)
        worker = User.objects.create_user("u", "u@mail.com", "123", organization=org)

        c = Comment.objects.create(worker=worker, task=task, text="Hello", organization=org)
        self.assertIn("Hello", str(c))

    def test_chatroom_default_name(self):
        org = Organization.objects.create(name="Org")
        room = ChatRoom.objects.create(organization=org)
        self.assertTrue(room.name.startswith("Group "))

    def test_chatroom_is_private(self):
        org = Organization.objects.create(name="Org")
        room = ChatRoom.objects.create(name="private_x", organization=org)
        self.assertTrue(room.is_private())

    def test_chatroom_other_member(self):
        org = Organization.objects.create(name="Org")
        w1 = User.objects.create_user("a", "a@a.com", "123", organization=org)
        w2 = User.objects.create_user("b", "b@b.com", "123", organization=org)

        room = ChatRoom.objects.create(name="private_chat", organization=org)
        room.members.add(w1, w2)

        self.assertEqual(room.other_member(w1), w2)

    def test_message_str(self):
        org = Organization.objects.create(name="Org")
        sender = User.objects.create_user("a", "a@a.com", "123", organization=org)
        room = ChatRoom.objects.create(name="R1", organization=org)
        msg = Message.objects.create(sender=sender, content="Hi", room=room, organization=org)

        self.assertIn("Hi", str(msg))

    def test_feedback_str(self):
        fb = Feedback.objects.create(
            name="John",
            email="john@mail.com",
            message="Hello!"
        )
        self.assertEqual(str(fb), "Feedback from John: john@mail.com")