# 📌 Ubicación en servidor: /home/pablollh/app/chatbot/extractors.py
import os
import rdflib 
import requests
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class ESCOExtractor:
    """
    Clase para manejar extracciones desde la API de ESCO
    """
    ESCO_API_BASE_URL = "https://ec.europa.eu/esco/api"

    def get_skills(self, language="en", limit=50):
        endpoint = "/resource/skill"
        params = {
            "language": language,
            "limit": limit
        }
        try:
            response = requests.get(f"{self.ESCO_API_BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener habilidades de ESCO: {e}")
            return None

    def get_occupations(self, language="en", limit=100, full=True):
        endpoint = "/resource/occupation"
        params = {
            "language": language,
            "limit": limit
        }
        try:
            response = requests.get(f"{self.ESCO_API_BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener ocupaciones de ESCO: {e}")
            return None

# ============== PARSE RDF DE ESCO (opcional) ==============
def parse_esco_rdf_to_json(rdf_path="esco.ttl", output_json="esco_from_rdf.json"):
    if not os.path.exists(rdf_path):
        logger.error(f"❌ Archivo RDF no encontrado: {rdf_path}")
        return
    try:
        g = rdflib.Graph()
        g.parse(rdf_path, format="turtle")
        sparql = """
        PREFIX esco: <http://data.europa.eu/esco/model#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?skill ?label WHERE {
          ?skill a esco:Skill .
          ?skill skos:prefLabel ?label .
          FILTER (lang(?label) = "es")
        }
        """
        results = g.query(sparql)
        esco_skills = {}
        for row in results:
            skill_uri = str(row.skill)
            label = str(row.label).strip().lower()
            skill_id = "ESCO_RDF_" + skill_uri.split("/")[-1]
            esco_skills[skill_id] = {
                "skill_name": label,
                "skill_type": "Hard Skill",
                "skill_len": len(label.split()),
                "high_surface_forms": {"full": label},
                "low_surface_forms": [label],
                "match_on_tokens": True
            }
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(esco_skills, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ {len(esco_skills)} skills de RDF guardados en {output_json}")
    except Exception as e:
        logger.error(f"❌ Error parseando RDF: {e}", exc_info=True)


def load_esco_ttl(ttl_path="esco.ttl"):
    """
    Carga el archivo Turtle (TTL) con rdflib y retorna un objeto Graph.
    """
    g = rdflib.Graph()
    g.parse(ttl_path, format="turtle")
    return g

def query_occupations(graph):
    """
    Ejemplo: Obtiene todas las ocupaciones y sus etiquetas preferidas en español.
    Ajusta el prefijo/esco:Skill/Occupation según la ontología ESCO.
    """
    # SPARQL de ejemplo
    #  - Filtra por 'esco:Occupation'
    #  - Extrae la URI ( ?occ ), y su 'skos:prefLabel' en español
    #  - Dependiendo de la estructura ESCO, revisa la doc u ontología
    #  - 'ESCO' define que una Occupation es 'a esco:Occupation'
    #  - 'prefLabel' se modela con 'skos:prefLabel'
    #  - Filtro lang(?label) = "es" para español
    query = """
    PREFIX esco: <http://data.europa.eu/esco/model#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?occ ?label
    WHERE {
      ?occ a esco:Occupation .
      ?occ skos:prefLabel ?label .
      FILTER(lang(?label) = "es")
    }
    LIMIT 100  # Solo 100 para ejemplo. Quita esta línea si quieres todos.
    """

    results = graph.query(query)
    occupations = []
    for row in results:
        occ_uri = str(row.occ)     # la URI
        label = str(row.label)     # la etiqueta preferida en español
        occupations.append({
            "uri": occ_uri,
            "preferredLabel_es": label
        })
    return occupations


class ONETExtractor:
    """
    Clase para manejar la extracción de datos desde O*NET Web Services.
    (Requiere registro y/o API Key)
    """
    ONET_API_BASE_URL = "https://services.onetcenter.org/ws/"

    def get_occupations(self, api_key, count=10):
        headers = {"Authorization": f"Bearer {api_key}"}
        endpoint = "occupations"
        params = {"end": count}
        try:
            response = requests.get(f"{self.ONET_API_BASE_URL}{endpoint}",
                                    headers=headers,
                                    params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener ocupaciones de O*NET: {e}")
            return None

    # Agrega métodos similares para 'skills', 'abilities', etc. según la API.


class NICEExtractor:
    """
    Clase para manejar la extracción de datos del NICE Framework
    (Generalmente desde un XLS/CSV que se descarga).
    """
    # URL de ejemplo; deberás usar la URL oficial donde se encuentra la hoja NICE
    NICE_DATA_URL = "https://ejemplo.gov/NICE_Framework.xlsx"
    NICE_LOCAL_PATH = "NICE_Framework.xlsx"

    def download_nice_file(self):
        """
        Descarga el archivo NICE si no existe ya en local.
        """
        if not os.path.exists(self.NICE_LOCAL_PATH):
            print("Descargando el archivo NICE...")
            try:
                response = requests.get(self.NICE_DATA_URL, stream=True)
                response.raise_for_status()
                with open(self.NICE_LOCAL_PATH, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("Descarga finalizada.")
            except requests.exceptions.RequestException as e:
                print(f"Error al descargar el archivo NICE: {e}")
        else:
            print("El archivo NICE ya está descargado en local.")

    def parse_nice_file(self, sheet_name="Skills"):
        """
        Parsea el archivo NICE (XLSX) y lo devuelve como lista de dicts (similar a JSON).
        """
        try:
            df = pd.read_excel(self.NICE_LOCAL_PATH, sheet_name=sheet_name)
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Error al leer/parsear el archivo NICE: {e}")
            return []

    def get_skills(self, sheet_name="Skills"):
        """
        Método principal: descarga el archivo si no está presente, 
        luego lo parsea y retorna los datos en formato dict.
        """
        self.download_nice_file()
        data = self.parse_nice_file(sheet_name=sheet_name)
        return data


class CareerOneStopExtractor:
    """
    Clase para manejar extracciones desde CareerOneStop.
    (Requiere registro y uso de credenciales)
    """
    CAREERONESTOP_API_BASE_URL = "https://api.careeronestop.org/v1/"

    def get_careers(self, api_user_id, api_key, keyword, limit=10):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "UserId": api_user_id
        }
        endpoint = f"careers/{keyword}"
        url = f"{self.CAREERONESTOP_API_BASE_URL}{endpoint}?limit={limit}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener datos de CareerOneStop: {e}")
            return None

class CONOCERExtractor:
    """
    Maneja la extracción de datos de las Normas de Competencia de CONOCER. Más un parser de PDF que un API.
    """

    def descargar_normas(self, lista_urls_pdfs):
        # Lógica para descargar PDFs y guardarlos localmente
        pass
    def parsear_norma(self, pdf_path):
        # Lógica para extraer texto de PDF con PyPDF2, pdfplumber, etc.
        # Retorna un dict con 'titulo_norma', 'competencias', etc.
        pass
    def generar_json_desde_normas(self, pdf_folder="normas_conocer"):
        # Recorre carpeta, parsea cada PDF y construye un JSON final
        conocer_data = []
        for archivo_pdf in os.listdir(pdf_folder):
            if archivo_pdf.endswith(".pdf"):
                ruta = os.path.join(pdf_folder, archivo_pdf)
                info = self.parsear_norma(ruta)
                conocer_data.append(info)
        # Al final, lo guardas en un JSON local
        out_file = "conocer_competencias.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(conocer_data, f, indent=2, ensure_ascii=False)

    def get_competencias(self):
        # Podrías incluso devolver la lista en memoria.
        pass

def unify_data(*datasets):
    """
    Ejemplo muy simple para unificar data de distintas fuentes en un formato genérico.
    Ajusta la lógica según la estructura JSON real de cada API/respuesta.
    """
    unified_list = []
    for data in datasets:
        if not data:
            continue
        
        # Dependiendo de si 'data' es dict, list, etc.
        if isinstance(data, list):
            # Ejemplo: NICEExtractor -> parsea XLS y retorna list de dicts
            for item in data:
                unified_list.append({
                    'source': 'NICE',
                    'type': 'skill',
                    'name': item.get('Skill Name', 'Sin nombre'),
                    'description': item.get('Description', 'Sin descripción')
                })
        elif isinstance(data, dict):
            # ESCO u otras APIs devuelven JSON con "_embedded" ...
            embedded = data.get("_embedded", {})
            if "occupation" in embedded:
                for occ in embedded["occupation"]:
                    unified_list.append({
                        'source': 'ESCO',
                        'type': 'occupation',
                        'name': occ.get("preferredLabel", "Sin nombre"),
                        'description': occ.get("description", "Sin desc")
                    })
            elif "skill" in embedded:
                for skill in embedded["skill"]:
                    unified_list.append({
                        'source': 'ESCO',
                        'type': 'skill',
                        'name': skill.get("preferredLabel", "Sin nombre"),
                        'description': skill.get("description", "Sin desc")
                    })
            else:
                # Caso O*NET, CareerOneStop, etc., 
                # analiza su estructura y normalízala también.
                pass
        else:
            # Cualquier otro caso
            pass

    return unified_list


def main():
    """
    Ejemplo de uso. En la práctica, podrías delegar esto a tu nlp.py
    o a un main.py orquestador.
    """
    esco_ext = ESCOExtractor()
    onet_ext = ONETExtractor()
    nice_ext = NICEExtractor()
    career_ext = CareerOneStopExtractor()

    # Llamadas de ejemplo
    esco_skills_data = esco_ext.get_skills(language="es", limit=5)
    nice_data = nice_ext.get_skills(sheet_name="Skills")
    # onet_data = onet_ext.get_occupations(api_key="TU_API_KEY_ONET", count=5)
    # career_data = career_ext.get_careers(api_user_id="USR_ID", api_key="API_KEY",
    #                                      keyword="cybersecurity", limit=5)

    # Unificamos lo que tengamos
    unified = unify_data(esco_skills_data, nice_data)
    print("Datos unificados:")
    for item in unified:
        print(item)


if __name__ == "__main__":
    main()