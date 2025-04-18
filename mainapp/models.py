from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """_summary_: This model is used to store all user details of the website """
    updated_at = models.DateTimeField(_("Is updated"), auto_now=True)
    role = models.CharField(
        max_length=25,
        choices=[
            ("manager", "Manager"),
            ("employee", "Employee"),
            ("superuser", "SuperUser")
        ],
        null=True, blank=True
    )
    # Adding custom related names to avoid conflict
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_("user groups"),
        related_name='user_groups',  # Custom related name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_("user permissions"),
        related_name='user_permissions',  # Custom related name
        blank=True
    )
    salary = models.BigIntegerField(default=0, blank=True, null=True)
    OTP = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} with role {self.role}"

    class Meta:
        verbose_name = _("User")
        ordering = ['-date_joined']


class Task(models.Model):
    """_summary_: This model is used to store all task details of the website """
    title = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    deadline = models.CharField(blank=True, null=True, max_length=25)
    priority = models.CharField(
        max_length=10,
        choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")],
        default="medium",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ManyToManyField(User, related_name='tasks')
    status = models.CharField(
        max_length=20,
        choices=[("accepted", "Accepted"), ("pending", "Pending"), ("rejected", "Rejected"),("completed", "Completed")],
        default="pending",
    )

    def __str__(self):
        return f"{self.title} "

    class Meta:
        verbose_name = _("Task")
        ordering = ['-created_at']


class Leaves(models.Model):
    """_summary_: This model is used to store all leaves details of the website """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(
        max_length=20, 
        choices=(('half_day', 'Half Day'), ('full_day', 'Full Day'), ('sick_leave', 'Sick Leave'), ('casual_leave', 'Casual Leave')), 
        blank=True, null=True
    )
    start_date = models.CharField(blank=True, null=True, max_length=25)
    end_date = models.CharField(blank=True, null=True, max_length=25)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[("accepted", "Accepted"), ("pending", "Pending"), ("rejected", "Rejected"),("completed", "Completed")],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.leave_type}"

    class Meta:
        verbose_name = _("Leave")
        ordering = ['-created_at']

