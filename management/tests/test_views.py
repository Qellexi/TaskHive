from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from soupsieve.css_parser import COMMENTS

from management.models import Organization, Worker, Task, Project, Team, ChatRoom, Comment, TaskType, Feedback

User = get_user_model()
TASKS = reverse("management:task-list")
PROJECTS = reverse("management:project-list")
TEAMS = reverse("management:team-list")
CHATROOMS = reverse("management:chat-list")
COMMENTS= reverse("management:comment-list")

# ---------------------------------------------------------------------
# Tests for register view
# ---------------------------------------------------------------------
class TestRegister(TestCase):
    def test_register_get(self):
        response = self.client.get(reverse("management:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/register.html")

    def test_register_post_valid(self):
        org = Organization.objects.create(name="Test org")
        response = self.client.post(reverse("management:register"),{
            "username": "testuser",
            "password": "12345",
            "email": "test@email.com",
            "first_name": "test_name",
            "last_name": "test_last_name",
            "organization": org.id,
        })
        self.assertEqual(Worker.objects.count(), 1)
        self.assertEqual(response.status_code, 302)

# ---------------------------------------------------------------------
# Tests for index view
# ---------------------------------------------------------------------
class TestIndex(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            username="test_user",
            password="12345",
            organization=self.org
        )

    def test_index_requires_login(self):
        response = self.client.get(reverse("management:index"))
        self.assertEqual(response.status_code, 302)

    def test_index_get_logged_in(self):
        self.client.login(username="test_user", password="12345")
        response = self.client.get(reverse("management:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "management/index.html")

    def test_index_post_valid(self):
        self.client.login(username="test_user", password="12345")
        response = self.client.post(reverse("management:index"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("num_workers", response.context)
# ---------------------------------------------------------------------
# Tests for WorkerListView/WorkerDetailView
# ---------------------------------------------------------------------
class WorkerTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="test_user",
            password="<PASSWORD>",
            organization=self.org
        )
        self.client.force_login(self.user)

    def test_worker_list_filters_by_organizations(self):
        other_org = Organization.objects.create(name="Other Org")
        Worker.objects.create(username="other", password="12345", organization=other_org)

        response = self.client.get(reverse("management:worker-list"))
        workers = response.context["worker_list"]
        for worker in workers:
            self.assertEqual(worker.organization, self.user.organization)
# ---------------------------------------------------------------------
# Tests for TaskListView/TaskDetailView
# ---------------------------------------------------------------------
class TaskListViewTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="test_user",
            password="<PASSWORD>",
            organization=self.org
        )
        self.client.force_login(self.user)


def test_retreat_tasks(self):
        Task.objects.create(name="Define models")
        Task.objects.create(name="Draw db")
        response = self.client.get(TASKS)
        self.assertEqual(response.status_code, 200)
        tasks = Task.objects.all()
        self.assertEqual(
            list(response.context["task_list"]),
            list(tasks),
        )
        self.assertTemplateUsed(response, "management/task_list.html")

# ---------------------------------------------------------------------
# Tests for ProjectListView/ProjectDetailView
# ---------------------------------------------------------------------
class ProjectListViewTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="test_user",
            password="<PASSWORD>",
            organization=self.org
        )
        self.client.force_login(self.user)


    def test_retreat_projects(self):
        team = Team.objects.create(name="Team1", organization=self.org)
        team.workers.add(self.user)
        p1 = Project.objects.create(name="Mobile app")
        p2 = Project.objects.create(name="Taxi manager")

        p1.teams.add(team)
        p2.teams.add(team)
        response = self.client.get(PROJECTS)
        self.assertEqual(response.status_code, 200)
        projects = Project.objects.all()
        self.assertEqual(
            list(response.context["project_list"]),
            list(projects),
        )
        self.assertTemplateUsed(response, "management/project_list.html")

# ---------------------------------------------------------------------
# Tests for TeamListView/TeamDetailView
# ---------------------------------------------------------------------
class TeamListViewTests(TestCase):
    def setUp(self) -> None:
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="test_user",
            password="<PASSWORD>",
            organization=self.org
        )
        self.client.force_login(self.user)


    def test_retreat_teams(self):
        team1 = Team.objects.create(name="Dev team", organization=self.org)
        Project.objects.create(name="Managers", organization=self.org)
        team2 = Team.objects.create(name="QA team", organization=self.org)
        response = self.client.get(TEAMS)
        self.assertEqual(response.status_code, 200)
        teams = Team.objects.filter(organization=self.org)
        self.assertEqual(
            list(response.context["team_list"]),
            list(teams),
        )
        self.assertTemplateUsed(response, "management/team_list.html")


# ---------------------------------------------------------------------
# Tests ChatRoomListView
# ---------------------------------------------------------------------
class ChatRoomListViewTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user1 = User.objects.create_user("u1", "u1@test.com", "12345", organization=self.org)
        self.user2 = User.objects.create_user("u2", "u2@test.com", "12345", organization=self.org)

        self.room = ChatRoom.objects.create(name="private_1_2", organization=self.org)
        self.room.members.add(self.user1, self.user2)

        self.client.force_login(self.user1)

    def test_chat_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("management:chat-list"))
        self.assertEqual(response.status_code, 302)

    def test_chat_list_shows_user_chats(self):
        response = self.client.get(reverse("management:chat-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.room, response.context["chat_list"])

    def test_chat_list_sets_other_user(self):
        response = self.client.get(reverse("management:chat-list"))
        chat = response.context["chat_list"][0]

        self.assertEqual(chat.other_user, self.user2)

# ---------------------------------------------------------------------
# Tests for CommentListView
# ---------------------------------------------------------------------
class CommentListViewTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user("u1", "u1@test.com", "12345", organization=self.org)
        self.other = User.objects.create_user("u2", "u2@test.com", "12345", organization=self.org)

        self.project = Project.objects.create(name="P1", organization=self.org)
        self.task = Task.objects.create(
            name="Task1", description="d", project=self.project,
            type=TaskType.objects.create(name="Bug"), organization=self.org
        )
        self.task.workers.add(self.user)

        # Comment from other user
        self.comment = Comment.objects.create(
            worker=self.other, task=self.task, text="Hi", organization=self.org
        )

        self.client.force_login(self.user)

    def test_comment_list_filters_by_user_tasks(self):
        response = self.client.get(reverse("management:comment-list"))
        self.assertEqual(response.status_code, 200)

        comments = response.context["comment_list"]
        self.assertIn(self.comment, comments)

    def test_comment_list_excludes_own_comments(self):
        own_comment = Comment.objects.create(
            worker=self.user, task=self.task, text="mine", organization=self.org
        )

        response = self.client.get(reverse("management:comment-list"))
        comments = response.context["comment_list"]

        self.assertNotIn(own_comment, comments)

# ---------------------------------------------------------------------
# Tests for feedback_view
# ---------------------------------------------------------------------
class FeedbackViewTests(TestCase):

    def test_feedback_post_creates_record(self):
        response = self.client.post(reverse("management:feedback"), {
            "name": "John",
            "email": "john@mail.com",
            "message": "Hello"
        })

        self.assertEqual(response.status_code, 302)

        self.assertEqual(Feedback.objects.count(), 1)

# ---------------------------------------------------------------------
# Tests for CRUD
# ---------------------------------------------------------------------
class TaskCreateViewTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            "u", "u@mail.com", "12345", organization=self.org
        )
        self.client.force_login(self.user)

        self.project = Project.objects.create(
            name="P1", organization=self.org
        )
        self.type = TaskType.objects.create(
            name="Bug", color="#ff0000"
        )

    def test_task_create_assigns_organization(self):
        self.client.post(
            reverse("management:task-create"),
            {
                "name": "NewTask",
                "description": "Desc",
                "project": self.project.id,
                "priority": "urgent",
                "status": "todo",

                "type": self.type.id,
                "create_new_type": False,
                "deadline": "2025-01-01",
                "workers": [],
            },
        )

        task = Task.objects.get(name="NewTask")
        self.assertEqual(task.organization, self.org)

class TaskUpdateViewTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            "u", "u@mail.com", "12345", organization=self.org
        )
        self.client.force_login(self.user)

        self.type = TaskType.objects.create(
            name="Bug", color="#ff0000"
        )

        self.task = Task.objects.create(
            name="Old",
            description="d",
            project=Project.objects.create(
                name="P1", organization=self.org
            ),
            type=self.type,
            organization=self.org,
        )

    def test_task_update(self):
        self.client.post(
            reverse(
                "management:task-update",
                kwargs={"pk": self.task.pk}
            ),
            {
                "name": "Updated",
                "description": "Changed",
                "project": self.task.project.id,
                "priority": "urgent",
                "status": "todo",

                "type": self.type.id,
                "create_new_type": False,
                "deadline": "2025-01-01",
                "workers": [],
            },
        )

        self.task.refresh_from_db()
        self.assertEqual(self.task.name, "Updated")

class TaskDeleteViewTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user("u", "u@mail.com", "12345", organization=self.org)
        self.client.force_login(self.user)

        self.task = Task.objects.create(
            name="DeleteMe",
            description="d",
            project=Project.objects.create(name="P1", organization=self.org),
            type=TaskType.objects.create(name="Bug"),
            organization=self.org,
        )

    def test_task_delete(self):
        response = self.client.post(reverse("management:task-delete", kwargs={"pk": self.task.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())


class TeamCRUDTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            "u", "u@mail.com", "12345", organization=self.org
        )
        self.client.force_login(self.user)

        self.team = Team.objects.create(name="Team1", organization=self.org)

    def test_team_create(self):
        response = self.client.post(reverse("management:team-create"), {
            "name": "NewTeam",
            "workers": [],
            "project": [],
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Team.objects.filter(name="NewTeam").exists())

    def test_team_update(self):
        response = self.client.post(
            reverse("management:team-update", kwargs={"pk": self.team.pk}),
            {"name": "UpdatedTeam", "workers": [], "project": []}
        )
        self.assertEqual(response.status_code, 302)

        self.team.refresh_from_db()
        self.assertEqual(self.team.name, "UpdatedTeam")

    def test_team_delete(self):
        response = self.client.post(
            reverse("management:team-delete", kwargs={"pk": self.team.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Team.objects.filter(pk=self.team.pk).exists())

class ProjectCRUDTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            "u", "u@test.com", "12345", organization=self.org
        )
        self.client.force_login(self.user)

        self.project = Project.objects.create(name="P1", organization=self.org)

    def test_project_create(self):
        response = self.client.post(reverse("management:project-create"), {
            "name": "NewProject",
            "description": "",
            "deadline": "2025-01-01",
            "teams": [],
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name="NewProject").exists())

    def test_project_update(self):
        response = self.client.post(
            reverse("management:project-update", kwargs={"pk": self.project.pk}),
            {"name": "UpdatedProject", "deadline": "2025-01-01"}
        )
        self.assertEqual(response.status_code, 302)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "UpdatedProject")

    def test_project_delete(self):
        response = self.client.post(
            reverse("management:project-delete", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())


class WorkerCRUDTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")
        self.user = User.objects.create_user(
            username="worker",
            email="worker@mail.com",
            password="12345",
            organization=self.org
        )
        self.client.force_login(self.user)

    def test_worker_update(self):
        response = self.client.post(
            reverse("management:worker-update", kwargs={"pk": self.user.pk}),
            {
                "first_name": "NewName",
                "last_name": "Last",
                "email": self.user.email,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "NewName")

    def test_worker_delete(self):
        response = self.client.post(
            reverse("management:worker-delete", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Worker.objects.filter(pk=self.user.pk).exists())


class DeleteCommentTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Org")

        self.user = User.objects.create_user(
            "u1", "u1@test.com", "12345", organization=self.org
        )
        self.other = User.objects.create_user(
            "u2", "u2@test.com", "12345", organization=self.org
        )

        self.project = Project.objects.create(name="P1", organization=self.org)
        self.task = Task.objects.create(
            name="Task1",
            description="d",
            project=self.project,
            type=TaskType.objects.create(name="Bug"),
            organization=self.org,
        )

        self.comment = Comment.objects.create(
            worker=self.other,
            task=self.task,
            text="text",
            organization=self.org
        )

        self.client.force_login(self.user)

    def test_user_cannot_delete_others_comment(self):
        response = self.client.post(
            reverse("management:delete_comment", kwargs={"comment_id": self.comment.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_user_can_delete_own_comment(self):
        my_comment = Comment.objects.create(
            worker=self.user, task=self.task, text="mine", organization=self.org
        )

        response = self.client.post(
            reverse("management:delete_comment", kwargs={"comment_id": my_comment.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=my_comment.pk).exists())
