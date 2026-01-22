import calendar
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max, Q, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.views.generic import TemplateView

from management.forms import WorkerRegistrationForm, WorkerUpdateForm, ChatGroupForm, TaskForm, \
    ProjectForm, TeamForm, CommentForm, SearchForm, FeedbackForm
from management.models import Worker, Task, Project, Comment, Organization, Team, ChatRoom

from datetime import date


def register(request):
    if request.method == "POST":
        form = WorkerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            login(request, user)
            return redirect("management:index")
    else:
        form = WorkerRegistrationForm()

    return render(request, "registration/register.html", {"form": form})

class OrganizationScopedMixin:
    """
    A mixin that filters queryset by the current user's organization.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.user.organization)


@login_required
def assign_organization(request):
    if request.method == "POST":
        org_id = request.POST.get("organization")
        if org_id:
            org = Organization.objects.get(id=org_id)
            request.user.organization = org
            request.user.save()
            return redirect("management:index")

    orgs = Organization.objects.all()
    return render(request, "management/organization_form.html", {"organizations": orgs})


@login_required
def index(request):
    num_workers = Worker.objects.all().count()
    num_visits = request.session.get('num_visits', 0)
    request.session["num_visits"] = num_visits + 1

    project_id = request.GET.get("project")
    selected_project = None
    if project_id:
        selected_project = Project.objects.get(id=project_id)
    cal_view = CalendarView()
    cal_view.request = request
    calendar_context = cal_view.get_context_data(selected_project=selected_project)
    calendar_defaults = {
        "days": [],
        "weeks": [],
        "weekday_names": [],
        "num_padding_days": 0,
        "month": None,
        "year": None,
        "month_name": "",
        "prev_month": None,
        "next_month": None,
        "tasks_by_day": {},
        "selected_day": None,
    }

    for key, default in calendar_defaults.items():
        calendar_context.setdefault(key, default)

    tasks = Task.objects.all()

    if selected_project:
        tasks = tasks.filter(project=selected_project)
        workers = Worker.objects.filter(tasks__in=tasks).distinct().annotate(
            done_tasks_count=Count("tasks", filter=Q(tasks__status="done")),
            tasks_count=Count("tasks")
        )
    else:
        workers = Worker.objects.annotate(
            done_tasks_count=Count("tasks", filter=Q(tasks__status="done")),
            tasks_count=Count("tasks")
        )

    num_tasks = tasks.count()
    num_tasks_done = tasks.filter(status__icontains="done").count()
    num_tasks_todo = tasks.exclude(status__icontains="done").count()
    datapoints = [
        {
            "label": f"{worker.first_name} {worker.last_name}",
            "y": f"{worker.tasks_count}"
        }
        for worker in workers
    ]
    priority_counts = [
        {"label": "Urgent", "y": tasks.filter(priority="urgent").count()},
        {"label": "Medium", "y": tasks.filter(priority="medium").count()},
        {"label": "Low", "y": tasks.filter(priority="low").count()},
    ]
    context = {
        "num_visits": num_visits,
        "num_workers": num_workers,
        "project_list": Project.objects.all(),
        "workers": workers,
        "selected_project": selected_project,
        "num_tasks": num_tasks,
        "num_tasks_done": num_tasks_done,
        "num_tasks_todo": num_tasks_todo,
        "datapoints": datapoints,
        "priority_counts": priority_counts,
        **calendar_context,
    }
    return render(request, "management/index.html", context)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)          # ← КЛЮЧОВЕ
            return redirect("management:index")
        else:
            return render(
                request,
                "registration/login.html",
                {"error": "Invalid username or password"}
            )

    return render(request, "registration/login.html")
@login_required
def profile(request):
    return render(request, "management/profile.html")

@login_required
def chat_view(request):
    return render(request, "management/chat.html")

@login_required
def chat_room(request, pk):
    room = ChatRoom.objects.get(pk=pk)
    return render(request, "management/chat.html", {"room": room})



class WorkerListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = Worker
    template_name = "management/worker_list.html"
    context_object_name = "worker_list"
    queryset = model.objects.order_by("id")
    paginate_by = 20

    # def get_context_data(self, **kwargs):
    #     context = super(WorkerListView, self)
    #
    #     return context


class WorkerDetailView(LoginRequiredMixin, OrganizationScopedMixin, generic.DetailView):
    model = Worker

class TaskListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = Task
    template_name = "management/task_list.html"
    context_object_name = "task_list"
    queryset = model.objects.order_by("id")
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        context["query"] = query
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search tasks..."

        tasks = self.model.objects.filter(workers=self.request.user)

        COLORS = {
            Task.Status.todo: "#3498db",
            Task.Status.in_progress: "#f1c40f",
            Task.Status.done: "#2ecc71",
        }

        status_groups = [
            {
                "label": label,
                "value": value,
                "tasks": tasks.filter(status=value),
                "color": COLORS.get(value, "#ccc")
            }
            for value, label in Task.Status.choices
        ]
        context["status_groups"] = status_groups
        return context

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        qs = super().get_queryset()
        if form.is_valid():
            query = form.cleaned_data.get("query")
            if query:
                qs = qs.filter(name__icontains=query)
        return qs

class TaskDetailView(LoginRequiredMixin, OrganizationScopedMixin, generic.DetailView):
    model = Task


class ProjectListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = Project
    template_name = "management/project_list.html"
    context_object_name = "project_list"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = Project.objects.filter(teams__workers=user).distinct()

        form = SearchForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get("query")
            if q:
                qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search projects..."
        context["query"] = query
        return context

class ProjectDetailView(LoginRequiredMixin, OrganizationScopedMixin, generic.DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        tasks = self.object.task_set.all()
        query = self.request.GET.get("query", "")
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search tasks..."
        if query:
            tasks = tasks.filter(name__icontains=query)
        context["tasks"] = tasks
        return context


class TeamListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = Team
    template_name = "management/team_list.html"
    context_object_name = "team_list"
    queryset = model.objects.order_by("id")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        context["query"] = query
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search teams..."
        return context

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        qs = super().get_queryset()
        if form.is_valid():
            query = form.cleaned_data.get("query")
            if query:
                qs = qs.filter(name__icontains=query)
        return qs

class TeamDetailView(LoginRequiredMixin, OrganizationScopedMixin, generic.DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get("query", "")
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search worker..."

        workers = self.object.workers.all()

        if query:
            parts = query.split()

            if len(parts) == 1:
                workers = workers.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )
            elif len(parts) >= 2:
                workers = workers.filter(
                    Q(first_name__icontains=parts[0]) &
                    Q(last_name__icontains=parts[1])
                )

        context["workers"] = workers
        return context


class ChatRoomListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = ChatRoom
    template_name = "management/chat.html"
    context_object_name = "chat_list"
    paginate_by = 10

    def get_queryset(self):
        qs = (ChatRoom.objects.filter(members=self.request.user)
              .annotate(last_message=Max("chats__timestamp"))
              .order_by("-last_message")
              .distinct())
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chats = context['chat_list']
        user = self.request.user

        for chat in chats:
            if chat.is_private():
                chat.other_user = chat.other_member(user)
            else:
                chat.other_user = None

        return context

class CommentListView(LoginRequiredMixin, OrganizationScopedMixin, generic.ListView):
    model = Comment
    template_name = "management/comment_list.html"
    context_object_name = "comment_list"
    queryset = model.objects.order_by("-created_at")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        context["query"] = query
        context["search_form"] = SearchForm(initial={"query": query})
        context["search_form"].fields["query"].widget.attrs["placeholder"] = "Search comments..."
        return context

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        qs = super().get_queryset()
        if form.is_valid():
            query = form.cleaned_data.get("query")
            if query:
                qs = qs.filter(
                    Q(worker__username__icontains=query) |
                    Q(worker__first_name__icontains=query) |
                    Q(worker__last_name__icontains=query) |
                    Q(task__name__icontains=query)
                )
        return qs.exclude(worker=self.request.user).filter(task__workers=self.request.user)


class CalendarView(TemplateView):
    def get_context_data(self, **kwargs):
        selected_project = kwargs.get("selected_project")
        context = super().get_context_data(**kwargs)

        start_date = date.today()
        month = int(self.request.GET.get("month", start_date.month))
        year = int(self.request.GET.get("year", start_date.year))

        num_days = calendar.monthrange(year, month)[1]
        days = [date(year, month, day) for day in range(1, num_days + 1)]

        user = self.request.user
        if user.is_authenticated:
            tasks = Task.objects.filter(
                deadline__date__gte=days[0],
                deadline__date__lte=days[-1],
                workers=user,
            ).order_by("deadline")
        else:
            tasks = Task.objects.none()

        if selected_project:
            tasks = tasks.filter(project=selected_project)

        tasks_by_day = {d: [] for d in days}
        for task in tasks:
            tasks_by_day[task.deadline.date()].append(task)

        first_day = date(year, month, 1)
        num_padding_days = first_day.weekday()
        prev_month_last_day = first_day - timedelta(days=1)
        next_month_first_day = date(year, month, num_days) + timedelta(days=1)
        selected_day_str = self.request.GET.get("day")
        if selected_day_str:
            selected_day = datetime.strptime(selected_day_str, "%Y-%m-%d").date()
        else:
            selected_day = start_date

        padded_days = [None] * num_padding_days + days
        weeks = [padded_days[i:i + 7] for i in range(0, len(padded_days), 7)]
        weekday_names = [calendar.day_abbr[i] for i in range(7)]
        month_name = calendar.month_name[month]
        context.update({
            "days": days,
            "tasks_by_day": tasks_by_day,
            "month": month,
            "month_name": month_name,
            "year": year,
            "num_padding_days": num_padding_days,
            "prev_month": {
                "month": prev_month_last_day.month,
                "year": prev_month_last_day.year,
            },
            "next_month": {
                "month": next_month_first_day.month,
                "year": next_month_first_day.year,
            },
            "now": start_date,
            "selected_day": selected_day,
            "weeks": weeks,
            'weekday_names': weekday_names,
        })
        return context


class AboutView(TemplateView):
    template_name = "management/about.html"
    def get_context_data(selfself, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback_form'] = FeedbackForm()
        return context

def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect("management:about")
    else:
        form = FeedbackForm()
    return render(request, "management/about.html", {
        "feedback_form": form
    })

#----CREATE VIEWS----
class CommentCreateView(LoginRequiredMixin, OrganizationScopedMixin, generic.CreateView):
    model = Comment


class OrganizationCreateView(LoginRequiredMixin, OrganizationScopedMixin, generic.CreateView):
    model = Organization
    fields = "__all__"
    template_name = "management/organization_form.html"

class TaskCreateView(LoginRequiredMixin, OrganizationScopedMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "management/task_form.html"
    success_url = reverse_lazy("management:task-list")

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class ProjectCreateView(LoginRequiredMixin, OrganizationScopedMixin, generic.CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "management/project_form.html"
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class TeamCreateView(LoginRequiredMixin, OrganizationScopedMixin, generic.CreateView):
    model = Team
    form_class = TeamForm
    template_name = "management/team_form.html"
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
class ChatRoomCreateView(LoginRequiredMixin, OrganizationScopedMixin, View):
    def get(self, request):
        group_form = ChatGroupForm()
        workers = Worker.objects.exclude(id=request.user.id)
        return render(request, "management/chat_form.html", {
            "group_form": group_form,
            "workers": workers,
        })

    def post(self, request):
        if "create_group" in request.POST:
            form = ChatGroupForm(request.POST)
            if form.is_valid():
                chat = form.save(commit=False)
                chat.organization = request.user.organization
                chat.save()
                form.save_m2m()
                return redirect("management:chat-list")
            workers = Worker.objects.exclude(id=request.user.id)
            return render(request, "management/chat_form.html", {
                "group_form": form,
                "workers": workers,
            })
        if "start_private" in request.POST:
            return self.start_private(request)

        return redirect("management:chat-create")

    def start_private(self, request):
        worker_id = request.POST.get("worker_id")
        user1 = request.user
        user2 = Worker.objects.get(pk=worker_id)

        chats = (
            ChatRoom.objects
            .filter(members=user1)
            .filter(members=user2)
            .distinct()
        )

        for chat in chats:
            if chat.members.count() == 2:
                return redirect("management:chat-list")

        chat = ChatRoom.objects.create(
            name=f"private_{user1.id}_{user2.id}",
            organization=request.user.organization,
        )
        chat.members.add(user1, user2)
        return redirect("management:chat-list")


@login_required
def add_comment(request, task_id):
    task = Task.objects.get(id=task_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.worker = request.user
            comment.organization = task.project.organization
            comment.save()
    return redirect("management:project-detail", pk=task.project.pk)


#----UPDATE VIEWS----
class WorkerUpdateView(LoginRequiredMixin, OrganizationScopedMixin, generic.UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    success_url = reverse_lazy("management:worker-list")

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, OrganizationScopedMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy("management:project-list")

class TaskUpdateView(LoginRequiredMixin, OrganizationScopedMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "management/task_form.html"
    success_url = reverse_lazy("management:task-list")

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class TeamUpdateView(LoginRequiredMixin, OrganizationScopedMixin, generic.UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "management/team_form.html"
    success_url = reverse_lazy("management:team-list")


#----DELETE VIEWS----
class ProjectDeleteView(LoginRequiredMixin, OrganizationScopedMixin, generic.DeleteView):
    model = Project
    success_url = reverse_lazy("management:project-list")
    template_name = "management/project_confirm_delete.html"

class WorkerDeleteView(LoginRequiredMixin, OrganizationScopedMixin, generic.DeleteView):
    model = Worker
    success_url = reverse_lazy("management:worker-list")
    template_name = "management/worker_confirm_delete.html"

class TaskDeleteView(LoginRequiredMixin, OrganizationScopedMixin, generic.DeleteView):
    model = Task
    success_url = reverse_lazy("management:task-list")
    template_name = "management/task_confirm_delete.html"

class TeamDeleteView(LoginRequiredMixin, OrganizationScopedMixin, generic.DeleteView):
    model = Team
    success_url = reverse_lazy("management:team-list")
    template_name = "management/team_confirm_delete.html"

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.worker: # not request.user.is_staff - make it with admin
        messages.error(request, "You cannot delete this comment.")
        return redirect("management:project-detail", pk=comment.task.project.id)

    project_id = comment.task.project.id
    comment.delete()
    messages.success(request, "Comment deleted successfully.")
    return redirect("management:project-detail", pk=project_id)

