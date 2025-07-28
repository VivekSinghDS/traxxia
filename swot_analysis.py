import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re

class SWOTNewsAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        
        # Keywords for SWOT categorization
        self.swot_keywords = {
            'strengths': [
                'growth', 'profit', 'revenue', 'success', 'innovation', 'leadership',
                'market share', 'competitive advantage', 'strong performance',
                'expansion', 'breakthrough', 'award', 'achievement'
            ],
            'weaknesses': [
                'loss', 'decline', 'problem', 'issue', 'challenge', 'weakness',
                'struggled', 'failed', 'deficit', 'shortfall', 'criticism',
                'controversy', 'lawsuit', 'recall'
            ],
            'opportunities': [
                'opportunity', 'potential', 'emerging', 'new market', 'partnership',
                'acquisition', 'expansion', 'trend', 'demand', 'investment',
                'collaboration', 'technology adoption', 'market entry'
            ],
            'threats': [
                'threat', 'competition', 'rival', 'regulation', 'risk', 'concern',
                'challenge', 'disruption', 'economic downturn', 'tariff',
                'sanctions', 'cyber attack', 'data breach'
            ]
        }
    
    def fetch_news(self, query, days_back=7, language='en'):
        """Fetch news articles from NewsAPI"""
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        params = {
            'q': query,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': language,
            'sortBy': 'relevancy',
            'pageSize': 100,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return None
    
    def categorize_article(self, title, description):
        """Categorize article into SWOT categories based on keywords"""
        text = f"{title} {description}".lower()
        scores = defaultdict(int)
        
        for category, keywords in self.swot_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    scores[category] += 1
        
        # Return category with highest score, or 'neutral' if no matches
        if scores:
            return max(scores, key=scores.get)
        return 'neutral'
    
    def analyze_sentiment_keywords(self, text):
        """Simple sentiment analysis based on positive/negative keywords"""
        positive_words = ['good', 'great', 'excellent', 'positive', 'strong', 'success']
        negative_words = ['bad', 'poor', 'negative', 'weak', 'failure', 'decline']
        
        text = text.lower()
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def generate_swot_analysis(self, company_name, days_back=7):
        """Generate SWOT analysis for a company"""
        print(f"Fetching news for {company_name}...")
        
        # Fetch news data
        news_data = self.fetch_news(company_name, days_back)
        if not news_data or news_data.get('status') != 'ok':
            print("Failed to fetch news data")
            return None
        
        articles = news_data.get('articles', [])
        print(f"Found {len(articles)} articles")
        
        # Categorize articles
        swot_analysis = {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'threats': [],
            'neutral': []
        }
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '') or ''
            
            category = self.categorize_article(title, description)
            sentiment = self.analyze_sentiment_keywords(f"{title} {description}")
            
            article_summary = {
                'title': title,
                'description': description[:200] + "..." if len(description) > 200 else description,
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'sentiment': sentiment,
                'source': article.get('source', {}).get('name', 'Unknown')
            }
            
            swot_analysis[category].append(article_summary)
        
        return swot_analysis
    
    def generate_swot_report(self, swot_analysis, company_name):
        """Generate formatted SWOT analysis report as text string"""
        report_lines = []
        
        # Header
        report_lines.append("=" * 60)
        report_lines.append(f"SWOT ANALYSIS REPORT FOR {company_name.upper()}")
        report_lines.append("=" * 60)
        
        categories = ['strengths', 'weaknesses', 'opportunities', 'threats']
        
        for category in categories:
            report_lines.append(f"\n{category.upper()}:")
            report_lines.append("-" * 40)
            
            articles = swot_analysis[category]
            if not articles:
                report_lines.append("No relevant articles found.")
                continue
            
            for i, article in enumerate(articles[:5], 1):  # Show top 5 per category
                report_lines.append(f"\n{i}. {article['title']}")
                report_lines.append(f"   Source: {article['source']}")
                report_lines.append(f"   Sentiment: {article['sentiment']}")
                report_lines.append(f"   Description: {article['description']}")
                report_lines.append(f"   URL: {article['url']}")
        
        # Summary statistics
        report_lines.append(f"\n{'=' * 60}")
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("=" * 60)
        
        for category in categories:
            count = len(swot_analysis[category])
            report_lines.append(f"{category.capitalize()}: {count} articles")
        
        total_articles = sum(len(swot_analysis[cat]) for cat in categories)
        report_lines.append(f"Total analyzed articles: {total_articles}")
        
        return "\n".join(report_lines)

# Example usage
if __name__ == "__main__":
    # You need to get your API key from https://newsapi.org/
    API_KEY = "d1b3658c875546baa970b0ff36887ac3"
    
    # Initialize analyzer
    analyzer = SWOTNewsAnalyzer(API_KEY)

    # here are some of the questions and answers for the kasnet, 
    # here are some of the information about the competitors
    # using both of the information, give me a swot analysis for the kasnet
    for company in [ 'BCP',"IBM", "Accenture", "Cognizant", "Capgemini"]:
    # Analyze a company
    # company = "Tesla"  # Change to any company you want to analyze
        swot_data = analyzer.generate_swot_analysis(company, days_back=14)
        
        if swot_data:
            result = ''
            analyzer.print_swot_report(swot_data, company)
            # result += swot_data['threats'] + '\n' + swot_data['strengths'] + '\n' + swot_data['opportunities'] + '\n' + swot_data['weaknesses'] + '\n'
            # You can also access the raw data
            print(f"\nStrengths found: {len(swot_data['strengths'])}")
            print(f"Weaknesses found: {len(swot_data['weaknesses'])}")
            print(f"Opportunities found: {len(swot_data['opportunities'])}")
            print(f"Threats found: {len(swot_data['threats'])}")
        else:
            print("Failed to generate SWOT analysis")
            
    