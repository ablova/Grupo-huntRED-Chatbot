"""
Complete Web Scraping Tasks for Ghuntred-v2
Advanced scraping capabilities for social media, job boards, and company data
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
import time
import random
from dataclasses import dataclass
from enum import Enum

from celery import shared_task
from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ScrapingType(Enum):
    """Types of scraping operations"""
    SOCIAL_MEDIA = "social_media"
    JOB_BOARDS = "job_boards"
    COMPANY_INFO = "company_info"
    SALARY_DATA = "salary_data"
    MARKET_ANALYSIS = "market_analysis"
    COMPETITOR_ANALYSIS = "competitor_analysis"


@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    source: str
    data_type: str
    data: Dict[str, Any]
    scraped_at: datetime
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.delay_range = (1, 3)  # Random delay between requests
    
    def get_page(self, url: str, **kwargs) -> requests.Response:
        """Get page with error handling and rate limiting"""
        try:
            # Random delay to avoid being blocked
            time.sleep(random.uniform(*self.delay_range))
            
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'html.parser')
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters
        text = re.sub(r'[^\w\s\-.,!?]', '', text)
        return text


class SocialMediaScraper(BaseScraper):
    """Scraper for social media platforms"""
    
    async def scrape_linkedin_profile(self, profile_url: str) -> ScrapingResult:
        """Scrape LinkedIn profile data"""
        try:
            # Note: LinkedIn has strict anti-scraping measures
            # This is a simplified example for demonstration
            
            response = self.get_page(profile_url)
            soup = self.parse_html(response.text)
            
            # Extract basic profile information
            name = self.extract_linkedin_name(soup)
            headline = self.extract_linkedin_headline(soup)
            location = self.extract_linkedin_location(soup)
            experience = self.extract_linkedin_experience(soup)
            education = self.extract_linkedin_education(soup)
            
            data = {
                "name": name,
                "headline": headline,
                "location": location,
                "experience": experience,
                "education": education,
                "profile_url": profile_url,
                "scraped_sections": ["basic_info", "experience", "education"]
            }
            
            return ScrapingResult(
                source="linkedin",
                data_type="profile",
                data=data,
                scraped_at=datetime.now(),
                success=True,
                metadata={"profile_completeness": self.calculate_profile_completeness(data)}
            )
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profile {profile_url}: {e}")
            return ScrapingResult(
                source="linkedin",
                data_type="profile",
                data={},
                scraped_at=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def extract_linkedin_name(self, soup: BeautifulSoup) -> str:
        """Extract name from LinkedIn profile"""
        name_selectors = [
            'h1.text-heading-xlarge',
            '.pv-text-details__left-panel h1',
            '.top-card-layout__title'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_linkedin_headline(self, soup: BeautifulSoup) -> str:
        """Extract headline from LinkedIn profile"""
        headline_selectors = [
            '.text-body-medium.break-words',
            '.pv-text-details__left-panel .text-body-medium',
            '.top-card-layout__headline'
        ]
        
        for selector in headline_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_linkedin_location(self, soup: BeautifulSoup) -> str:
        """Extract location from LinkedIn profile"""
        location_selectors = [
            '.text-body-small.inline.t-black--light.break-words',
            '.pv-text-details__left-panel .text-body-small',
            '.top-card__subline-item'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element and 'location' in element.get_text().lower():
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_linkedin_experience(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract experience from LinkedIn profile"""
        experience = []
        
        # Look for experience section
        experience_section = soup.find('section', {'id': 'experience-section'}) or \
                           soup.find('div', {'id': 'experience'})
        
        if experience_section:
            jobs = experience_section.find_all('div', class_='pv-entity__summary-info')
            
            for job in jobs[:5]:  # Limit to 5 most recent
                title_elem = job.find('h3')
                company_elem = job.find('p', class_='pv-entity__secondary-title')
                duration_elem = job.find('h4', class_='pv-entity__date-range')
                
                if title_elem:
                    experience.append({
                        "title": self.clean_text(title_elem.get_text()),
                        "company": self.clean_text(company_elem.get_text()) if company_elem else "",
                        "duration": self.clean_text(duration_elem.get_text()) if duration_elem else ""
                    })
        
        return experience
    
    def extract_linkedin_education(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract education from LinkedIn profile"""
        education = []
        
        # Look for education section
        education_section = soup.find('section', {'id': 'education-section'}) or \
                          soup.find('div', {'id': 'education'})
        
        if education_section:
            schools = education_section.find_all('div', class_='pv-entity__summary-info')
            
            for school in schools[:3]:  # Limit to 3 most recent
                school_elem = school.find('h3')
                degree_elem = school.find('p', class_='pv-entity__secondary-title')
                years_elem = school.find('p', class_='pv-entity__dates')
                
                if school_elem:
                    education.append({
                        "school": self.clean_text(school_elem.get_text()),
                        "degree": self.clean_text(degree_elem.get_text()) if degree_elem else "",
                        "years": self.clean_text(years_elem.get_text()) if years_elem else ""
                    })
        
        return education
    
    def calculate_profile_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate profile completeness score"""
        fields = ["name", "headline", "location", "experience", "education"]
        completed = sum(1 for field in fields if data.get(field))
        return (completed / len(fields)) * 100
    
    async def scrape_twitter_profile(self, username: str) -> ScrapingResult:
        """Scrape Twitter profile data"""
        try:
            # Twitter requires API access for reliable scraping
            # This is a simplified example
            
            profile_url = f"https://twitter.com/{username}"
            response = self.get_page(profile_url)
            soup = self.parse_html(response.text)
            
            # Extract basic information
            data = {
                "username": username,
                "display_name": self.extract_twitter_name(soup),
                "bio": self.extract_twitter_bio(soup),
                "location": self.extract_twitter_location(soup),
                "followers_count": self.extract_twitter_followers(soup),
                "following_count": self.extract_twitter_following(soup),
                "tweet_count": self.extract_twitter_tweets(soup),
                "profile_url": profile_url
            }
            
            return ScrapingResult(
                source="twitter",
                data_type="profile",
                data=data,
                scraped_at=datetime.now(),
                success=True,
                metadata={"engagement_estimate": self.estimate_twitter_engagement(data)}
            )
            
        except Exception as e:
            logger.error(f"Error scraping Twitter profile {username}: {e}")
            return ScrapingResult(
                source="twitter",
                data_type="profile",
                data={},
                scraped_at=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def extract_twitter_name(self, soup: BeautifulSoup) -> str:
        """Extract display name from Twitter profile"""
        name_selectors = [
            '[data-testid="UserName"] span',
            '.ProfileHeaderCard-name a',
            'h1[role="heading"]'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_twitter_bio(self, soup: BeautifulSoup) -> str:
        """Extract bio from Twitter profile"""
        bio_selectors = [
            '[data-testid="UserDescription"]',
            '.ProfileHeaderCard-bio',
            '.css-901oao.css-16my406'
        ]
        
        for selector in bio_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_twitter_location(self, soup: BeautifulSoup) -> str:
        """Extract location from Twitter profile"""
        location_selectors = [
            '[data-testid="UserLocation"]',
            '.ProfileHeaderCard-location',
            'span[data-testid="UserLocation"]'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def extract_twitter_followers(self, soup: BeautifulSoup) -> int:
        """Extract followers count from Twitter profile"""
        followers_selectors = [
            'a[href$="/followers"] span',
            '.ProfileNav-item--followers .ProfileNav-value',
            '[data-testid="UserFollowers"] span'
        ]
        
        for selector in followers_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                return self.parse_count(text)
        
        return 0
    
    def extract_twitter_following(self, soup: BeautifulSoup) -> int:
        """Extract following count from Twitter profile"""
        following_selectors = [
            'a[href$="/following"] span',
            '.ProfileNav-item--following .ProfileNav-value',
            '[data-testid="UserFollowing"] span'
        ]
        
        for selector in following_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                return self.parse_count(text)
        
        return 0
    
    def extract_twitter_tweets(self, soup: BeautifulSoup) -> int:
        """Extract tweet count from Twitter profile"""
        tweets_selectors = [
            '.ProfileNav-item--tweets .ProfileNav-value',
            '[data-testid="UserTweets"] span'
        ]
        
        for selector in tweets_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                return self.parse_count(text)
        
        return 0
    
    def parse_count(self, text: str) -> int:
        """Parse count from text (handles K, M suffixes)"""
        text = text.replace(',', '').strip()
        
        if 'K' in text.upper():
            return int(float(text.upper().replace('K', '')) * 1000)
        elif 'M' in text.upper():
            return int(float(text.upper().replace('M', '')) * 1000000)
        else:
            try:
                return int(re.sub(r'[^\d]', '', text))
            except ValueError:
                return 0
    
    def estimate_twitter_engagement(self, data: Dict[str, Any]) -> str:
        """Estimate engagement level based on followers/following ratio"""
        followers = data.get("followers_count", 0)
        following = data.get("following_count", 0)
        
        if followers == 0:
            return "low"
        
        ratio = followers / max(following, 1)
        
        if ratio > 10:
            return "high"
        elif ratio > 2:
            return "medium"
        else:
            return "low"


class JobBoardScraper(BaseScraper):
    """Scraper for job boards and salary data"""
    
    async def scrape_indeed_jobs(self, search_query: str, location: str = "Mexico") -> ScrapingResult:
        """Scrape job postings from Indeed"""
        try:
            base_url = "https://mx.indeed.com/jobs"
            params = {
                'q': search_query,
                'l': location,
                'limit': 50
            }
            
            response = self.get_page(base_url, params=params)
            soup = self.parse_html(response.text)
            
            jobs = []
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:20]:  # Limit to 20 jobs
                job_data = self.extract_indeed_job_data(card)
                if job_data:
                    jobs.append(job_data)
            
            data = {
                "search_query": search_query,
                "location": location,
                "total_jobs": len(jobs),
                "jobs": jobs,
                "scraped_url": response.url
            }
            
            return ScrapingResult(
                source="indeed",
                data_type="job_listings",
                data=data,
                scraped_at=datetime.now(),
                success=True,
                metadata={"average_salary": self.calculate_average_salary(jobs)}
            )
            
        except Exception as e:
            logger.error(f"Error scraping Indeed jobs: {e}")
            return ScrapingResult(
                source="indeed",
                data_type="job_listings",
                data={},
                scraped_at=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def extract_indeed_job_data(self, card) -> Optional[Dict[str, Any]]:
        """Extract job data from Indeed job card"""
        try:
            title_elem = card.find('h2', class_='jobTitle')
            company_elem = card.find('span', class_='companyName')
            location_elem = card.find('div', class_='companyLocation')
            salary_elem = card.find('span', class_='salaryText')
            summary_elem = card.find('div', class_='job-snippet')
            
            # Extract job URL
            link_elem = title_elem.find('a') if title_elem else None
            job_url = urljoin("https://mx.indeed.com", link_elem['href']) if link_elem else ""
            
            return {
                "title": self.clean_text(title_elem.get_text()) if title_elem else "",
                "company": self.clean_text(company_elem.get_text()) if company_elem else "",
                "location": self.clean_text(location_elem.get_text()) if location_elem else "",
                "salary": self.clean_text(salary_elem.get_text()) if salary_elem else "",
                "summary": self.clean_text(summary_elem.get_text()) if summary_elem else "",
                "url": job_url,
                "posted_date": datetime.now().strftime("%Y-%m-%d")  # Indeed doesn't always show dates
            }
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
    
    def calculate_average_salary(self, jobs: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate average salary from job listings"""
        salaries = []
        
        for job in jobs:
            salary_text = job.get("salary", "")
            if salary_text:
                salary_range = self.parse_salary_range(salary_text)
                if salary_range:
                    salaries.extend(salary_range)
        
        return sum(salaries) / len(salaries) if salaries else None
    
    def parse_salary_range(self, salary_text: str) -> Optional[List[float]]:
        """Parse salary range from text"""
        # Remove currency symbols and normalize
        text = re.sub(r'[,$]', '', salary_text)
        
        # Look for salary ranges
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:a|to|-)\s*(\d+(?:\.\d+)?)', text)
        if range_match:
            min_salary = float(range_match.group(1))
            max_salary = float(range_match.group(2))
            
            # Convert to monthly if needed
            if 'hora' in salary_text.lower() or 'hour' in salary_text.lower():
                min_salary *= 40 * 4.33  # 40 hours/week * 4.33 weeks/month
                max_salary *= 40 * 4.33
            elif 'año' in salary_text.lower() or 'year' in salary_text.lower():
                min_salary /= 12
                max_salary /= 12
            
            return [min_salary, max_salary]
        
        # Look for single salary
        single_match = re.search(r'(\d+(?:\.\d+)?)', text)
        if single_match:
            salary = float(single_match.group(1))
            
            # Convert to monthly if needed
            if 'hora' in salary_text.lower() or 'hour' in salary_text.lower():
                salary *= 40 * 4.33
            elif 'año' in salary_text.lower() or 'year' in salary_text.lower():
                salary /= 12
            
            return [salary]
        
        return None


class CompanyInfoScraper(BaseScraper):
    """Scraper for company information and market data"""
    
    async def scrape_company_info(self, company_name: str, website_url: str) -> ScrapingResult:
        """Scrape company information from website"""
        try:
            response = self.get_page(website_url)
            soup = self.parse_html(response.text)
            
            # Extract company information
            data = {
                "company_name": company_name,
                "website_url": website_url,
                "title": self.extract_page_title(soup),
                "description": self.extract_meta_description(soup),
                "industry": self.extract_industry_info(soup),
                "contact_info": self.extract_contact_info(soup),
                "social_links": self.extract_social_links(soup),
                "technologies": self.extract_technologies(soup),
                "employee_count_estimate": self.estimate_company_size(soup)
            }
            
            return ScrapingResult(
                source="company_website",
                data_type="company_info",
                data=data,
                scraped_at=datetime.now(),
                success=True,
                metadata={"page_analysis": self.analyze_website_quality(soup)}
            )
            
        except Exception as e:
            logger.error(f"Error scraping company info for {company_name}: {e}")
            return ScrapingResult(
                source="company_website",
                data_type="company_info",
                data={},
                scraped_at=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_elem = soup.find('title')
        return self.clean_text(title_elem.get_text()) if title_elem else ""
    
    def extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ""
    
    def extract_industry_info(self, soup: BeautifulSoup) -> str:
        """Extract industry information from content"""
        # Look for industry keywords in content
        industry_keywords = [
            'tecnología', 'software', 'desarrollo', 'consultoría',
            'finanzas', 'salud', 'educación', 'manufactura',
            'retail', 'e-commerce', 'marketing', 'publicidad'
        ]
        
        text = soup.get_text().lower()
        found_industries = [keyword for keyword in industry_keywords if keyword in text]
        
        return ', '.join(found_industries[:3]) if found_industries else ""
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract contact information"""
        contact_info = {}
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            contact_info['email'] = emails[0]
        
        # Look for phone numbers
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, soup.get_text())
        if phones:
            contact_info['phone'] = ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        
        return contact_info
    
    def extract_social_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        social_links = {}
        social_domains = {
            'facebook.com': 'facebook',
            'twitter.com': 'twitter',
            'linkedin.com': 'linkedin',
            'instagram.com': 'instagram',
            'youtube.com': 'youtube'
        }
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            for domain, platform in social_domains.items():
                if domain in href:
                    social_links[platform] = href
                    break
        
        return social_links
    
    def extract_technologies(self, soup: BeautifulSoup) -> List[str]:
        """Extract technology stack information"""
        tech_keywords = [
            'python', 'javascript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'aws',
            'azure', 'docker', 'kubernetes', 'mongodb', 'postgresql'
        ]
        
        text = soup.get_text().lower()
        found_tech = [tech for tech in tech_keywords if tech in text]
        
        return found_tech
    
    def estimate_company_size(self, soup: BeautifulSoup) -> str:
        """Estimate company size based on website content"""
        text = soup.get_text().lower()
        
        # Look for size indicators
        if any(word in text for word in ['startup', 'pequeña', 'small']):
            return "1-50"
        elif any(word in text for word in ['mediana', 'medium', 'growing']):
            return "51-200"
        elif any(word in text for word in ['grande', 'large', 'enterprise']):
            return "201-1000"
        elif any(word in text for word in ['multinacional', 'global', 'worldwide']):
            return "1000+"
        else:
            return "unknown"
    
    def analyze_website_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze website quality metrics"""
        return {
            "has_meta_description": bool(soup.find('meta', attrs={'name': 'description'})),
            "has_title": bool(soup.find('title')),
            "image_count": len(soup.find_all('img')),
            "link_count": len(soup.find_all('a')),
            "has_contact_info": bool(re.search(r'@|contact|contacto', soup.get_text(), re.IGNORECASE)),
            "mobile_friendly": bool(soup.find('meta', attrs={'name': 'viewport'}))
        }


# Celery Tasks

@shared_task(bind=True, max_retries=3, default_retry_delay=120, queue='scraping')
async def ejecutar_scraping(self, business_unit_id: Optional[int] = None, scraping_type: str = "all"):
    """Execute comprehensive scraping operations"""
    try:
        logger.info(f"Starting scraping task for business unit {business_unit_id}, type: {scraping_type}")
        
        results = []
        
        if scraping_type in ["all", "social_media"]:
            # Social media scraping
            social_scraper = SocialMediaScraper()
            
            # Example LinkedIn profiles (would come from database)
            linkedin_profiles = [
                "https://linkedin.com/in/example1",
                "https://linkedin.com/in/example2"
            ]
            
            for profile_url in linkedin_profiles:
                result = await social_scraper.scrape_linkedin_profile(profile_url)
                results.append(result)
            
            # Example Twitter profiles
            twitter_usernames = ["example1", "example2"]
            
            for username in twitter_usernames:
                result = await social_scraper.scrape_twitter_profile(username)
                results.append(result)
        
        if scraping_type in ["all", "job_boards"]:
            # Job board scraping
            job_scraper = JobBoardScraper()
            
            # Search for relevant jobs
            search_queries = ["desarrollador python", "analista de datos", "gerente de recursos humanos"]
            
            for query in search_queries:
                result = await job_scraper.scrape_indeed_jobs(query, "Ciudad de México")
                results.append(result)
        
        if scraping_type in ["all", "company_info"]:
            # Company information scraping
            company_scraper = CompanyInfoScraper()
            
            # Example companies (would come from database)
            companies = [
                {"name": "Empresa Ejemplo 1", "website": "https://ejemplo1.com"},
                {"name": "Empresa Ejemplo 2", "website": "https://ejemplo2.com"}
            ]
            
            for company in companies:
                result = await company_scraper.scrape_company_info(
                    company["name"], 
                    company["website"]
                )
                results.append(result)
        
        # Process and store results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        summary = {
            "total_operations": len(results),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "scraping_type": scraping_type,
            "business_unit_id": business_unit_id,
            "completed_at": datetime.now().isoformat()
        }
        
        # Store results in database (mock implementation)
        await store_scraping_results(results, business_unit_id)
        
        logger.info(f"Scraping task completed: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error in scraping task: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying scraping task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "error": str(e),
            "retries": self.request.retries,
            "scraping_type": scraping_type,
            "business_unit_id": business_unit_id
        }


@shared_task(bind=True, queue='scraping')
async def scrape_social_media_profiles(self, employee_id: str, social_profiles: Dict[str, str]):
    """Scrape social media profiles for specific employee"""
    try:
        logger.info(f"Scraping social profiles for employee {employee_id}")
        
        social_scraper = SocialMediaScraper()
        results = []
        
        for platform, profile_url in social_profiles.items():
            if platform.lower() == "linkedin":
                result = await social_scraper.scrape_linkedin_profile(profile_url)
            elif platform.lower() == "twitter":
                # Extract username from URL
                username = profile_url.split('/')[-1]
                result = await social_scraper.scrape_twitter_profile(username)
            else:
                continue
            
            results.append(result)
        
        # Generate analysis report
        analysis = generate_social_analysis(results)
        
        return {
            "employee_id": employee_id,
            "platforms_analyzed": len(results),
            "successful_scrapes": len([r for r in results if r.success]),
            "analysis": analysis,
            "scraped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scraping social profiles for employee {employee_id}: {e}")
        return {
            "employee_id": employee_id,
            "success": False,
            "error": str(e)
        }


@shared_task(bind=True, queue='scraping')
async def scrape_market_salary_data(self, job_title: str, location: str = "Mexico"):
    """Scrape salary data for market analysis"""
    try:
        logger.info(f"Scraping salary data for {job_title} in {location}")
        
        job_scraper = JobBoardScraper()
        
        # Scrape from multiple sources
        indeed_result = await job_scraper.scrape_indeed_jobs(job_title, location)
        
        # Analyze salary data
        salary_analysis = analyze_salary_data([indeed_result])
        
        return {
            "job_title": job_title,
            "location": location,
            "salary_analysis": salary_analysis,
            "data_sources": ["indeed"],
            "scraped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scraping salary data for {job_title}: {e}")
        return {
            "job_title": job_title,
            "location": location,
            "success": False,
            "error": str(e)
        }


@shared_task(bind=True, queue='scraping')
async def monitor_competitor_jobs(self, competitor_companies: List[str]):
    """Monitor job postings from competitor companies"""
    try:
        logger.info(f"Monitoring job postings for competitors: {competitor_companies}")
        
        job_scraper = JobBoardScraper()
        competitor_data = []
        
        for company in competitor_companies:
            result = await job_scraper.scrape_indeed_jobs(f"company:{company}")
            if result.success:
                competitor_data.append({
                    "company": company,
                    "job_count": result.data.get("total_jobs", 0),
                    "jobs": result.data.get("jobs", [])
                })
        
        # Analyze competitor hiring trends
        trends = analyze_competitor_trends(competitor_data)
        
        return {
            "competitors_monitored": len(competitor_companies),
            "total_jobs_found": sum(c["job_count"] for c in competitor_data),
            "trends": trends,
            "competitor_data": competitor_data,
            "monitored_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoring competitor jobs: {e}")
        return {
            "competitors_monitored": len(competitor_companies),
            "success": False,
            "error": str(e)
        }


# Helper Functions

async def store_scraping_results(results: List[ScrapingResult], business_unit_id: Optional[int]):
    """Store scraping results in database"""
    # Mock implementation - would store in actual database
    logger.info(f"Storing {len(results)} scraping results for business unit {business_unit_id}")
    
    for result in results:
        # Would insert into database table
        logger.debug(f"Stored {result.source} {result.data_type} result")


def generate_social_analysis(results: List[ScrapingResult]) -> Dict[str, Any]:
    """Generate analysis from social media scraping results"""
    analysis = {
        "profile_completeness_avg": 0,
        "platforms_active": 0,
        "professional_score": 0,
        "red_flags": [],
        "strengths": []
    }
    
    successful_results = [r for r in results if r.success]
    
    if not successful_results:
        return analysis
    
    # Calculate averages and scores
    completeness_scores = []
    platforms = []
    
    for result in successful_results:
        platforms.append(result.source)
        
        if result.source == "linkedin":
            completeness = result.metadata.get("profile_completeness", 0)
            completeness_scores.append(completeness)
            
            # Check for professional indicators
            data = result.data
            if data.get("experience"):
                analysis["strengths"].append("Has professional experience listed")
            if data.get("education"):
                analysis["strengths"].append("Education background provided")
        
        elif result.source == "twitter":
            engagement = result.metadata.get("engagement_estimate", "low")
            if engagement == "high":
                analysis["strengths"].append("High social media engagement")
    
    analysis["profile_completeness_avg"] = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
    analysis["platforms_active"] = len(set(platforms))
    analysis["professional_score"] = min(100, analysis["profile_completeness_avg"] + (analysis["platforms_active"] * 10))
    
    return analysis


def analyze_salary_data(results: List[ScrapingResult]) -> Dict[str, Any]:
    """Analyze salary data from scraping results"""
    analysis = {
        "average_salary": 0,
        "salary_range": {"min": 0, "max": 0},
        "total_jobs": 0,
        "data_quality": "low"
    }
    
    all_salaries = []
    total_jobs = 0
    
    for result in results:
        if result.success and result.data_type == "job_listings":
            jobs = result.data.get("jobs", [])
            total_jobs += len(jobs)
            
            for job in jobs:
                salary_text = job.get("salary", "")
                if salary_text:
                    # Parse salary (simplified)
                    salary_numbers = re.findall(r'\d+', salary_text.replace(',', ''))
                    if salary_numbers:
                        all_salaries.extend([float(s) for s in salary_numbers])
    
    if all_salaries:
        analysis["average_salary"] = sum(all_salaries) / len(all_salaries)
        analysis["salary_range"]["min"] = min(all_salaries)
        analysis["salary_range"]["max"] = max(all_salaries)
        analysis["data_quality"] = "high" if len(all_salaries) > 10 else "medium"
    
    analysis["total_jobs"] = total_jobs
    
    return analysis


def analyze_competitor_trends(competitor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze competitor hiring trends"""
    trends = {
        "most_active_company": "",
        "trending_roles": [],
        "average_jobs_per_company": 0,
        "growth_indicators": []
    }
    
    if not competitor_data:
        return trends
    
    # Find most active company
    most_active = max(competitor_data, key=lambda x: x["job_count"])
    trends["most_active_company"] = most_active["company"]
    
    # Calculate average
    total_jobs = sum(c["job_count"] for c in competitor_data)
    trends["average_jobs_per_company"] = total_jobs / len(competitor_data)
    
    # Analyze trending roles
    all_jobs = []
    for company_data in competitor_data:
        all_jobs.extend(company_data.get("jobs", []))
    
    # Count job titles
    title_counts = {}
    for job in all_jobs:
        title = job.get("title", "").lower()
        title_counts[title] = title_counts.get(title, 0) + 1
    
    # Get top trending roles
    trending_roles = sorted(title_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    trends["trending_roles"] = [{"title": title, "count": count} for title, count in trending_roles]
    
    # Growth indicators
    if total_jobs > len(competitor_data) * 10:
        trends["growth_indicators"].append("High hiring activity in market")
    
    return trends