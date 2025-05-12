# 📌 Ubicación en servidor: /home/pablo/app/com/chatbot/extractors.py
import os
import rdflib
import requests
import logging
import pandas as pd
import json

logger = logging.getLogger('nlp')

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
            logger.error(f"Error al obtener habilidades de ESCO: {e}")
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
            logger.error(f"Error al obtener ocupaciones de ESCO: {e}")
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
    Obtiene todas las ocupaciones y sus etiquetas preferidas en español.
    """
    query = """
    PREFIX esco: <http://data.europa.eu/esco/model#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT ?occ ?label
    WHERE {
      ?occ a esco:Occupation .
      ?occ skos:prefLabel ?label .
      FILTER(lang(?label) = "es")
    }
    LIMIT 100
    """
    results = graph.query(query)
    occupations = []
    for row in results:
        occ_uri = str(row.occ)
        label = str(row.label)
        occupations.append({
            "uri": occ_uri,
            "preferredLabel_es": label
        })
    return occupations

class ONETExtractor:
    """
    Clase para manejar la extracción de datos desde O*NET Web Services.
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
            logger.error(f"Error al obtener ocupaciones de O*NET: {e}")
            return None

class NICEExtractor:
    """
    Clase para manejar la extracción de datos del NICE Framework desde un archivo XLSX descargable.
    Optimiza el uso de CPU y soporta múltiples hojas del archivo.
    """
    # URL oficial del archivo NICE Framework Components (verificada en NIST)
    NICE_DATA_URL = "https://www.nist.gov/document/nice-framework-components-v100-xlsx"
    NICE_LOCAL_PATH = "NICE_Framework_Components.xlsx"

    def download_nice_file(self):
        """
        Descarga el archivo NICE solo si no existe localmente para minimizar uso de red.
        Usa streaming para manejar archivos grandes eficientemente.
        """
        if os.path.exists(self.NICE_LOCAL_PATH):
            logger.info(f"Archivo NICE ya existe en {self.NICE_LOCAL_PATH}")
            return
        logger.info(f"Descargando archivo NICE desde {self.NICE_DATA_URL}")
        try:
            response = requests.get(self.NICE_DATA_URL, stream=True, timeout=10)
            response.raise_for_status()
            with open(self.NICE_LOCAL_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Evita escribir chunks vacíos
                        f.write(chunk)
            logger.info(f"Descarga completada: {self.NICE_LOCAL_PATH}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al descargar el archivo NICE: {e}")
            raise

    def parse_nice_file(self, sheet_name="Skills"):
        """
        Parsea una hoja específica del archivo NICE XLSX usando pandas.
        Minimiza uso de memoria con openpyxl y manejo selectivo de columnas.
        """
        try:
            # Verifica que el archivo exista
            if not os.path.exists(self.NICE_LOCAL_PATH):
                logger.error(f"Archivo no encontrado: {self.NICE_LOCAL_PATH}")
                return []
            # Lee solo la hoja especificada para reducir uso de memoria
            df = pd.read_excel(
                self.NICE_LOCAL_PATH,
                sheet_name=sheet_name,
                engine='openpyxl',
                dtype=str  # Trata todo como string para evitar conversiones innecesarias
            )
            # Limpia datos: elimina filas vacías y normaliza nombres de columnas
            df = df.dropna(how='all').fillna('')
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            logger.info(f"Parseada hoja '{sheet_name}' con {len(df)} registros")
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error al parsear la hoja '{sheet_name}' del archivo NICE: {e}")
            return []

    def get_skills(self, sheet_name="Skills"):
        """
        Método principal: descarga el archivo si es necesario y retorna los datos parseados.
        """
        self.download_nice_file()
        data = self.parse_nice_file(sheet_name=sheet_name)
        if not data:
            logger.warning(f"No se obtuvieron datos de la hoja '{sheet_name}'")
        return data

class CareerOneStopExtractor:
    """
    Clase para manejar extracciones desde CareerOneStop.
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
            logger.error(f"Error al obtener datos de CareerOneStop: {e}")
            return None

class CONOCERExtractor:
    """
    Clase para manejar la extracción de datos de las Normas de Competencia de CONOCER.
    """
    def descargar_normas(self, lista_urls_pdfs):
        # Lógica para descargar PDFs y guardarlos localmente
        pass

    def parsear_norma(self, pdf_path):
        # Lógica para extraer texto de PDF con PyPDF2, pdfplumber, etc.
        pass

    def generar_json_desde_normas(self, pdf_folder="normas_conocer"):
        conocer_data = []
        for archivo_pdf in os.listdir(pdf_folder):
            if archivo_pdf.endswith(".pdf"):
                ruta = os.path.join(pdf_folder, archivo_pdf)
                info = self.parsear_norma(ruta)
                conocer_data.append(info)
        out_file = "conocer_competencias.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(conocer_data, f, indent=2, ensure_ascii=False)

    def get_competencias(self):
        pass

def unify_data(*datasets):
    """
    Unifica datos de múltiples fuentes en un formato genérico y normalizado.
    """
    unified_list = []
    for data in datasets:
        if not data:
            continue
        if isinstance(data, list):
            # NICEExtractor: lista de dicts desde XLSX
            for item in data:
                unified_list.append({
                    'source': 'NICE',
                    'type': 'skill',
                    'name': item.get('Skill Name', 'Sin nombre'),
                    'description': item.get('Description', 'Sin descripción')
                })
        elif isinstance(data, dict):
            # ESCO: JSON con "_embedded"
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
        return unified_list

def main():
    """
    Ejemplo de uso para probar los extractores.
    Configura logging y prueba NICEExtractor con una hoja específica.
    """
    # Configura logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Instancia extractores
    esco_ext = ESCOExtractor()
    nice_ext = NICEExtractor()

    # Obtener datos de prueba
    logger.info("Obteniendo habilidades de ESCO...")
    esco_skills_data = esco_ext.get_skills(language="es", limit=5)

    logger.info("Obteniendo habilidades de NICE...")
    nice_data = nice_ext.get_skills(sheet_name="Skills")  # Ajusta sheet_name según el XLSX

    # Unificar datos
    unified = unify_data(esco_skills_data, nice_data)
    logger.info("Datos unificados:")
    for item in unified[:5]:  # Limita a 5 para no saturar la salida
        logger.info(json.dumps(item, ensure_ascii=False))

if __name__ == "__main__":
    main()