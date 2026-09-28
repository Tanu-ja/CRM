from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    CLIENT_ADMIN = "CLIENT_ADMIN", "Client Manager"
    TELECALLER = "TELECALLER", "Telecaller"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", Role.TELECALLER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.SUPER_ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=20, choices=Role.choices)
    client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        related_name="users",
        on_delete=models.PROTECT,
        help_text="Null only for Super Admin.",
    )
    employee_id = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    joining_date = models.DateField(default=timezone.localdate)

    # Bumped whenever an admin force-resets this user's password, so a
    # middleware can invalidate any session established before that moment.
    session_valid_after = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["client", "employee_id"],
                name="unique_employee_id_per_client",
                condition=models.Q(employee_id__gt=""),
            ),
        ]
        indexes = [models.Index(fields=["client", "role"])]

    def __str__(self):
        return self.email

    @property
    def is_super_admin(self):
        return self.role == Role.SUPER_ADMIN

    @property
    def is_client_admin(self):
        return self.role == Role.CLIENT_ADMIN

    @property
    def is_telecaller(self):
        return self.role == Role.TELECALLER

    def mark_sessions_stale(self):
        self.session_valid_after = timezone.now()
        self.save(update_fields=["session_valid_after"])
