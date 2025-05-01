# /home/pablo/tests/test_linkedin.py
import asyncio
from app.utilidades.linkedin import process_csv
from app.models import BusinessUnit, Person
from asgiref.sync import sync_to_async

async def test_process_csv():
    business_unit = await sync_to_async(BusinessUnit.objects.get)(name="huntRED")
    sample_csv = "/tmp/connections.csv"
    with open(sample_csv, 'w', encoding='utf-8') as f:
        f.write("First Name,Last Name,Email Address,Company,Position\n")
        f.write("Juan,Pérez,juan@email.com,Acme,Analista de Datos\n")
    await process_csv(sample_csv, business_unit)
    candidate = await sync_to_async(Person.objects.filter(email="juan@email.com").first)()
    assert candidate, "Candidato no creado"
    assert candidate.metadata["position"] == "Analista de Datos", "Posición incorrecta"
    print("✅ CSV procesado")

if __name__ == "__main__":
    import django
    django.setup()
    asyncio.run(test_process_csv())