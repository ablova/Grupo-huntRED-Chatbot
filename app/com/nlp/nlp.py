class NLPProcessor:
    """
    Procesador avanzado de lenguaje natural para análisis de experiencia y habilidades.
    """
    
    def __init__(self):
        """Inicializa el procesador NLP."""
        self.nlp = spacy.load("es_core_news_lg")
        self.skill_patterns = self._load_skill_patterns()
        self.experience_analyzer = ExperienceAnalyzer()
        
    def _load_skill_patterns(self) -> Dict:
        """Carga patrones de reconocimiento de habilidades."""
        return {
            'technical': [
                r'\b(?:desarroll[oa]r?|implement[oa]r?|diseñ[oa]r?|cre[oa]r?)\s+(?:aplicaciones|sistemas|software|webs|apps)\b',
                r'\b(?:manej[oa]r?|gestion[oa]r?|administr[oa]r?)\s+(?:bases de datos|servidores|redes|infraestructura)\b',
                r'\b(?:program[oa]r?|codific[oa]r?)\s+(?:en|con)\s+(?:Python|Java|JavaScript|C\+\+|Ruby|PHP)\b'
            ],
            'soft': [
                r'\b(?:lider[oa]r?|dirig[oa]r?|coordin[oa]r?)\s+(?:equipos|proyectos|grupos)\b',
                r'\b(?:comunic[oa]r?|present[oa]r?|negoci[oa]r?)\s+(?:efectivamente|con clientes|con stakeholders)\b',
                r'\b(?:resolv[oa]r?|gestion[oa]r?)\s+(?:conflictos|problemas|crisis)\b'
            ],
            'domain': [
                r'\b(?:experiencia|conocimiento|dominio)\s+(?:en|de)\s+(?:finanzas|marketing|ventas|operaciones)\b',
                r'\b(?:especialista|experto|consultor)\s+(?:en|de)\s+(?:transformación digital|innovación|estrategia)\b'
            ]
        }
        
    async def analyze_experience(self, experience: Experience) -> Dict:
        """
        Analiza una experiencia laboral completa para extraer información detallada.
        
        Args:
            experience: Objeto Experience a analizar
            
        Returns:
            Dict con análisis detallado
        """
        try:
            # Procesar descripción con spaCy
            doc = self.nlp(experience.description)
            
            # Extraer habilidades técnicas
            technical_skills = self._extract_technical_skills(doc)
            
            # Extraer habilidades blandas
            soft_skills = self._extract_soft_skills(doc)
            
            # Extraer dominio específico
            domain_knowledge = self._extract_domain_knowledge(doc)
            
            # Analizar responsabilidades
            responsibilities = self._analyze_responsibilities(doc)
            
            # Analizar logros
            achievements = self._analyze_achievements(doc)
            
            # Calcular nivel de seniority
            seniority = self._calculate_seniority(
                experience.years,
                responsibilities,
                achievements
            )
            
            # Analizar impacto
            impact = self._analyze_impact(doc)
            
            return {
                'technical_skills': technical_skills,
                'soft_skills': soft_skills,
                'domain_knowledge': domain_knowledge,
                'responsibilities': responsibilities,
                'achievements': achievements,
                'seniority_level': seniority,
                'impact': impact,
                'skill_confidence': self._calculate_skill_confidence(
                    technical_skills,
                    soft_skills,
                    domain_knowledge
                )
            }
            
        except Exception as e:
            logger.error(f"Error analizando experiencia: {str(e)}")
            return {}
            
    def _extract_technical_skills(self, doc) -> List[Dict]:
        """Extrae habilidades técnicas del texto."""
        skills = []
        
        # Buscar patrones técnicos
        for pattern in self.skill_patterns['technical']:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                skill_text = match.group()
                # Extraer tecnología específica
                tech = self._extract_technology(skill_text)
                if tech:
                    skills.append({
                        'name': tech,
                        'context': skill_text,
                        'confidence': self._calculate_confidence(skill_text)
                    })
        
        # Buscar menciones de tecnologías
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'ORG']:
                skills.append({
                    'name': ent.text,
                    'context': ent.sent.text,
                    'confidence': 0.8
                })
                
        return skills
        
    def _extract_soft_skills(self, doc) -> List[Dict]:
        """Extrae habilidades blandas del texto."""
        skills = []
        
        # Buscar patrones de soft skills
        for pattern in self.skill_patterns['soft']:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                skill_text = match.group()
                skills.append({
                    'name': self._normalize_soft_skill(skill_text),
                    'context': skill_text,
                    'confidence': self._calculate_confidence(skill_text)
                })
                
        return skills
        
    def _extract_domain_knowledge(self, doc) -> List[Dict]:
        """Extrae conocimiento de dominio específico."""
        knowledge = []
        
        # Buscar patrones de dominio
        for pattern in self.skill_patterns['domain']:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                domain_text = match.group()
                knowledge.append({
                    'domain': self._normalize_domain(domain_text),
                    'context': domain_text,
                    'confidence': self._calculate_confidence(domain_text)
                })
                
        return knowledge
        
    def _analyze_responsibilities(self, doc) -> List[Dict]:
        """Analiza responsabilidades mencionadas."""
        responsibilities = []
        
        # Buscar frases que indiquen responsabilidad
        responsibility_patterns = [
            r'(?:responsable|encargado|a cargo)\s+(?:de|por)\s+([^\.]+)',
            r'(?:gestion[oa]r?|administr[oa]r?)\s+([^\.]+)',
            r'(?:lider[oa]r?|dirig[oa]r?)\s+([^\.]+)'
        ]
        
        for pattern in responsibility_patterns:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                resp_text = match.group(1)
                responsibilities.append({
                    'text': resp_text,
                    'type': self._classify_responsibility(resp_text),
                    'level': self._calculate_responsibility_level(resp_text)
                })
                
        return responsibilities
        
    def _analyze_achievements(self, doc) -> List[Dict]:
        """Analiza logros mencionados."""
        achievements = []
        
        # Buscar frases que indiquen logros
        achievement_patterns = [
            r'(?:increment[oa]r?|aument[oa]r?|mejor[oa]r?)\s+([^\.]+)',
            r'(?:reduc[oa]r?|optimiz[oa]r?|automatiz[oa]r?)\s+([^\.]+)',
            r'(?:implement[oa]r?|desarroll[oa]r?|cre[oa]r?)\s+([^\.]+)'
        ]
        
        for pattern in achievement_patterns:
            matches = re.finditer(pattern, doc.text, re.IGNORECASE)
            for match in matches:
                achievement_text = match.group(1)
                achievements.append({
                    'text': achievement_text,
                    'impact': self._calculate_achievement_impact(achievement_text),
                    'metrics': self._extract_metrics(achievement_text)
                })
                
        return achievements
        
    def _calculate_seniority(self, years: int, responsibilities: List[Dict], 
                           achievements: List[Dict]) -> str:
        """Calcula nivel de seniority basado en múltiples factores."""
        # Puntuación base por años
        score = min(years * 10, 100)
        
        # Ajustar por responsabilidades
        for resp in responsibilities:
            score += resp['level'] * 5
            
        # Ajustar por logros
        for achievement in achievements:
            score += achievement['impact'] * 10
            
        # Determinar nivel
        if score >= 80:
            return "Senior"
        elif score >= 60:
            return "Mid-Level"
        else:
            return "Junior"
            
    def _analyze_impact(self, doc) -> Dict:
        """Analiza el impacto general de la experiencia."""
        impact = {
            'scope': self._calculate_scope(doc),
            'complexity': self._calculate_complexity(doc),
            'innovation': self._calculate_innovation(doc),
            'leadership': self._calculate_leadership(doc)
        }
        
        return impact
        
    def _calculate_skill_confidence(self, technical: List[Dict], 
                                  soft: List[Dict], domain: List[Dict]) -> float:
        """Calcula nivel de confianza en la extracción de habilidades."""
        # Ponderar por tipo de habilidad
        weights = {
            'technical': 0.5,
            'soft': 0.3,
            'domain': 0.2
        }
        
        # Calcular confianza promedio por tipo
        tech_conf = sum(s['confidence'] for s in technical) / len(technical) if technical else 0
        soft_conf = sum(s['confidence'] for s in soft) / len(soft) if soft else 0
        domain_conf = sum(k['confidence'] for k in domain) / len(domain) if domain else 0
        
        # Combinar con pesos
        return (
            tech_conf * weights['technical'] +
            soft_conf * weights['soft'] +
            domain_conf * weights['domain']
        ) 