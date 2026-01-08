import random
import string
import uuid

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.db.transaction import commit
from django.forms import ModelForm

from .models import Worker, Organization, Project, ChatRoom, Task, Team, TaskType, Comment, Feedback

COLOR_CHOICES = [
    ("#ffd6d1", "Soft Red"),
    ("#fafaa3", "Pale Yellow"),
    ("#e2f8ff", "Sky Blue"),
    ("#d1ffe6", "Mint Green"),
    ("#f5ccff", "Lavender"),
    ("#ffeed6", "Peach"),
]


class WorkerRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(widget=forms.PasswordInput())
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        label="Company"
    )

    class Meta:
        model = Worker
        fields = ['username', 'email', 'password', 'organization']


class OrganizationForm(forms.ModelForm):
    existing_organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label="Choose existing Organization",
        widget=forms.Select(),
    )
    name = forms.CharField(
        max_length=100,
        required=False,
        label="Or create new Organization",
    )
    class Meta:
        model = Organization
        fields = ['name', 'code']

    def save(self, *args, **kwargs):
        if self.cleaned_data.get('existing_organization'):
            return self.cleaned_data['existing_organization']
        instance = super().save(commit=False)
        if not instance.name:
            instance.name = self.generate_default_name()
        if not instance.code:
            instance.code = self.generate_unique_code()
        if commit:
            instance.save()
        return instance
    def generate_unique_code(self):
        characters = string.ascii_letters + string.digits
        while True:
            code = "".join(random.choice(characters) for _ in range(8))
            if not Organization.objects.filter(code=code).exists():
                return code

    def generate_default_name(self):
        base_name = "Organization"
        existing_org = Organization.objects.filter(name__startswith=base_name).count()
        if existing_org == 0:
            return base_name
        else:
            return f"{base_name}-{existing_org + 1}"


class WorkerUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = Worker
        fields = (
            "first_name",
            "last_name",
            "email",
        )


class ProjectForm(ModelForm):
    teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    deadline = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        ),
        initial="2025-01-01",
    )
    class Meta:
        model = Project
        exclude = ("organization",)


class ChatGroupForm(ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    class Meta:
        model = ChatRoom
        fields = ["name", "members"]


class TaskForm(ModelForm):
    workers = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    type = forms.ModelChoiceField(
        queryset=TaskType.objects.all(),
        required=False,
        label="Choose existing type"
    )
    create_new_type = forms.BooleanField(
        required=False,
        label="Create new type?",
    )
    new_type_name = forms.CharField(
        required=False,
        label="New type name"
    )
    new_type_color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        label="New type color",
    )
    deadline = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "datetime-local",
            }
        ),
        initial="2025-01-01",
    )
    class Meta:
        model = Task
        fields = "__all__"
        exclude = ["organization"]

    field_order = [
        "name",
        "description",
        "is_completed",
        "type",
        "create_new_type",
        "new_type_name",
        "new_type_color",
    ]

    def clean(self):
        cleaned = super().clean()
        create_new = cleaned.get("create_new_type")
        selected_type = cleaned.get("type")

        if create_new:
            if not cleaned.get("new_type_name"):
                self.add_error("new_type_name", "Please enter a new type name.")

            if not cleaned.get("new_type_color"):
                self.add_error("new_type_color", "Please choose a new type color.")

        else:
            if not selected_type:
                self.add_error("type", "Select an existing type or choose to create new one.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('create_new_type'):
            new_type = TaskType.objects.create(
                name=self.cleaned_data['new_type_name'],
                color=self.cleaned_data["new_type_color"],
            )
            instance.type = new_type

        else:
            instance.type = self.cleaned_data["type"]

        if commit:
            instance.save()
            self.save_m2m()

        return instance

class TeamForm(ModelForm):
    workers = forms.ModelMultipleChoiceField(
        queryset=Worker.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    project = forms.ModelMultipleChoiceField(
        queryset=Project.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    class Meta:
        model = Team
        exclude = ("organization",)

    def save(self, commit=True):
        team = super().save(commit=commit)
        projects = self.cleaned_data["project"]
        if projects:
            for project in projects:
                project.teams.add(team)
        return team


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text",]
        widgets = {
            "text": forms.Textarea(
                attrs={"rows": 2, "placeholder": "Add a comment..."}
            )
        }


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search..."
            }
        )
    )

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["name", "email", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }