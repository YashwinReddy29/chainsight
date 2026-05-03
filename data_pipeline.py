"""
Data Pipeline: API Fetching, HTML Parsing, and Database Storage
Security-first implementation with exact version pinning
"""

import requests  # CHAINSIGHT-REVIEW
from bs4 import BeautifulSoup  # CHAINSIGHT-REVIEW
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
Base = declarative_base()


class ScrapedData(Base):
    """Model for storing scraped data"""
    __tablename__ = 'scraped_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False)
    title = Column(String(500))
    content = Column(Text)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    status_code = Column(Integer)


class DataPipeline:
    """Main data pipeline class for fetching, parsing, and storing data"""
    
    def __init__(self, db_url='sqlite:///scraped_data.db'):
        """
        Initialize the data pipeline
        
        Args:
            db_url: Database connection string (default: SQLite)
        """
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info(f"Database initialized: {db_url}")
    
    def fetch_data(self, url, timeout=30):
        """
        Fetch data from external API/URL
        
        Args:
            url: Target URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Response object or None if failed
        """
        try:
            headers = {
                'User-Agent': 'DataPipeline/1.0'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Successfully fetched data from {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from {url}: {e}")
            return None
    
    def parse_html(self, html_content):
        """
        Parse HTML content using BeautifulSoup
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            Dictionary with parsed data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else 'No title'
            
            # Extract main content (customize based on your needs)
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text content
            content = soup.get_text(separator=' ', strip=True)
            
            parsed_data = {
                'title': title_text,
                'content': content[:5000]  # Limit content length
            }
            
            logger.info(f"Successfully parsed HTML content")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            return {'title': 'Parse Error', 'content': str(e)}
    
    def save_to_database(self, url, parsed_data, status_code):
        """
        Save parsed data to database
        
        Args:
            url: Source URL
            parsed_data: Dictionary with parsed data
            status_code: HTTP status code
        """
        try:
            scraped_entry = ScrapedData(
                url=url,
                title=parsed_data.get('title', ''),
                content=parsed_data.get('content', ''),
                status_code=status_code
            )
            
            self.session.add(scraped_entry)
            self.session.commit()
            logger.info(f"Data saved to database for URL: {url}")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to save data to database: {e}")
    
    def run_pipeline(self, url):
        """
        Execute the complete pipeline: fetch -> parse -> save
        
        Args:
            url: Target URL to process
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"Starting pipeline for URL: {url}")
        
        # Step 1: Fetch data
        response = self.fetch_data(url)
        if not response:
            return False
        
        # Step 2: Parse HTML
        parsed_data = self.parse_html(response.text)
        
        # Step 3: Save to database
        self.save_to_database(url, parsed_data, response.status_code)
        
        logger.info(f"Pipeline completed successfully for URL: {url}")
        return True
    
    def get_all_records(self):
        """
        Retrieve all records from database
        
        Returns:
            List of ScrapedData objects
        """
        return self.session.query(ScrapedData).all()
    
    def close(self):
        """Close database session"""
        self.session.close()
        logger.info("Database session closed")


def main():
    """Example usage of the data pipeline"""
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Example URLs to scrape
    urls = [
        'https://example.com',
        'https://httpbin.org/html'
    ]
    
    # Run pipeline for each URL
    for url in urls:
        pipeline.run_pipeline(url)
    
    # Display results
    records = pipeline.get_all_records()
    print(f"\nTotal records in database: {len(records)}")
    for record in records:
        print(f"ID: {record.id}, URL: {record.url}, Title: {record.title}")
    
    # Cleanup
    pipeline.close()


if __name__ == '__main__':
    main()

# Made with Bob
