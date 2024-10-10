import datetime
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("ai-electionbot-firebase.json")  # Replace with the path to your service account key JSON file
firebase_admin.initialize_app(cred)
db = firestore.client()


def fetch_latest_articles():
    
    today = datetime.datetime.now()
    five_days_ago = today - datetime.timedelta(days=5)

    # Query for articles added in the last 5 days
    articles_ref = db.collection('news')
    recent_articles = articles_ref.where('date', '>=', five_days_ago).stream()

    return [article.to_dict() for article in recent_articles]

def summarize_articles(articles):

    summaries = "\n".join([f"{article['title']}: {article['summary']}" for article in articles])
    prompt = f"Summarize the following recent election articles to display in a web page: {summaries}"

    # Send to Vertex AI (ensure your bot integration here)
    response = get_election_update_from_chatbot(prompt)
    return response
