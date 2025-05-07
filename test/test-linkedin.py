# /home/pablo/test/test_linkedin.py
import pytest
from asgiref.sync import sync_to_async
from app.utilidades.linkedin import process_csv
from app.models import BusinessUnit, Person
import os

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_process_csv(tmp_path):
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    sample_csv = tmp_path / "connections.csv"
    sample_csv.write_text(
        "First Name,Last Name,Email Address,Company,Position\n"
        "Juan,Pérez,juan@email.com,Acme,Analista de Datos\n",
        encoding='utf-8'
    )
    await process_csv(str(sample_csv), business_unit)
    candidate = await sync_to_async(Person.objects.filter(email="juan@email.com").first)()
    assert candidate, "Candidato no creado"
    assert candidate.metadata["position"] == "Analista de Datos", "Posición incorrecta"