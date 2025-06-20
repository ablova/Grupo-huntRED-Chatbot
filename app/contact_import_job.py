"""Modelo ContactImportJob y registro en la app.

Colocado en un archivo separado para evitar editar el gigantesco app/models.py.
Se importa automáticamente cuando Django carga las clases admin (admin_contact_import)
por lo que el modelo queda registrado en la app sin tocar la lógica existente.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class ContactImportJob(models.Model):
    """Registro de ejecuciones de sincronización de contactos."""

    class Source(models.TextChoices):
        GOOGLE = "google_contacts", _("Google Contacts")
        ICLOUD = "icloud", _("iCloud")
        LINKEDIN = "linkedin", _("LinkedIn")
        CSV = "csv", _("CSV")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        DONE = "done", _("Done")
        ERROR = "error", _("Error")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_import_jobs",
        verbose_name=_("Triggered by"),
    )
    source = models.CharField(max_length=32, choices=Source.choices)
    file = models.FileField("CSV file", upload_to="imports/", blank=True, null=True)
    bu = models.CharField("Business Unit", max_length=32)

    total = models.PositiveIntegerField(default=0)
    added = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "status"]),
            models.Index(fields=["created_at", "status"]),
        ]
        verbose_name = "Contact Import Job"
        verbose_name_plural = "Contact Import Jobs"

    def __str__(self):
        return f"{self.get_source_display()} – {self.user} – {self.created_at:%Y-%m-%d %H:%M}"
