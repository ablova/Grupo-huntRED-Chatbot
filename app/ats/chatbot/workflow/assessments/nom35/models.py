from django.db import models
from app.models import Person, BusinessUnit

class AssessmentNOM35(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    responses = models.JSONField(default=dict, help_text="Respuestas del cuestionario NOM 35")
    score = models.IntegerField()
    risk_level = models.CharField(max_length=20)  # bajo, medio, alto
    date_taken = models.DateTimeField(auto_now_add=True)
    scheduled_by_onboarding = models.BooleanField(default=False, help_text="Si la evaluación fue agendada automáticamente por onboarding")
    scheduled_date = models.DateTimeField(null=True, blank=True, help_text="Fecha programada para el envío de la evaluación")

    class Meta:
        verbose_name = "Evaluación NOM 35"
        verbose_name_plural = "Evaluaciones NOM 35"
        ordering = ['-date_taken']

class AssessmentNOM35Result(models.Model):
    assessment = models.OneToOneField(AssessmentNOM35, on_delete=models.CASCADE)
    recommendations = models.TextField()
    report_pdf = models.FileField(upload_to='nom35_reports/', null=True, blank=True)

    class Meta:
        verbose_name = "Resultado NOM 35"
        verbose_name_plural = "Resultados NOM 35" 