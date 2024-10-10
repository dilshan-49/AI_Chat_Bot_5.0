import json
import firebase_admin
from firebase_admin import credentials, firestore
import urllib.request
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK
cred = credentials.Certificate("ai-electionbot-firebase.json")  # Replace with the path to your service account key JSON file
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()


apikey = "b1ab4df17fabe4a8d79fe19f7ad59d30"
today = datetime.today()
two_months_ago = today - timedelta(days=20)
from_date = two_months_ago.strftime('%Y-%m-%d')
to_date = today.strftime('%Y-%m-%d')

url = f"https://gnews.io/api/v4/search?q=Sri+Lanka+election+2024&lang=en&country=lk&from={from_date}&to={to_date}&max=10&apikey={apikey}"

def clean_content(content):
    # Remove HTML tags
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator="\n")
    
    # Remove unwanted patterns (e.g., advertisements, social media links)
    patterns_to_remove = [
        r'Advertisement',  # Example pattern for advertisements
        r'Follow us on\s+\w+',  # Example pattern for social media links
        r'Read all the Latest News',  # Example pattern for news links
        r'Find us on YouTube',  # Example pattern for YouTube links
        r'Most Searched Categories',  # Example pattern for categories
        r'Copyright @ \d{4}',  # Example pattern for copyright
        r'About Us',  # Example pattern for about us
        r'Contact Us',  # Example pattern for contact us
        r'Privacy Policy',  # Example pattern for privacy policy
        r'Cookie Policy',  # Example pattern for cookie policy
        r'Terms Of Use',  # Example pattern for terms of use
        r'Home',  # Example pattern for home
        r'Video',  # Example pattern for video
        r'Shorts',  # Example pattern for shorts
        r'News',  # Example pattern for news
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def fetch_article_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            article_html = response.read().decode("utf-8")
            soup = BeautifulSoup(article_html, 'html.parser')
            
            # Extract main content from the article
            main_content = None
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    json_data = json.loads(script.string)
                    if json_data.get('@type') == 'NewsArticle':
                        main_content = json_data.get('articleBody')
                        break
                except json.JSONDecodeError:
                    continue
            
            if main_content:
                return clean_content(main_content)
            else:
                # Fallback to extracting text from the main article body
                article_body = soup.find('div', class_='article-body')  # Adjust the class name based on the actual HTML structure
                if article_body:
                    return clean_content(article_body.get_text(separator="\n"))
                else:
                    return "Content not found"
    except Exception as e:
        return f"Failed to fetch content: {str(e)}"



def add_articles_to_firestore(articles_data):
 
    # Reference to the 'news' collection
    news_collection = db.collection('news')
    
    # Add each article to the 'news' collection
    for article in articles_data:
        # Check if a document with the same URL already exists
        existing_docs = news_collection.where('url', '==', article['url']).stream()
        if not any(existing_docs):
            news_collection.add(article)
        else:
            print(f"Article with URL {article['url']} already exists. Skipping.")
    
    print(f"Processed {len(articles_data)} articles.")

def main():
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        articles = data["articles"]

        articles_data = []

        for article in articles:
            article_info = {
                "title": article['title'],
                "url": article['url'],
                "content": fetch_article_content(article['url'])
            }
            articles_data.append(article_info)
    add_articles_to_firestore(articles_data)

if __name__ == "__main__":
    main()