from flask import Flask, render_template, send_from_directory, abort, jsonify
from markupsafe import Markup  # Import Markup from markupsafe
import os

app = Flask(__name__)

# News feed from the news folder
def get_news():
    news_folder = os.path.join(app.root_path, "news")
    news = []
    for folder in os.listdir(news_folder):
        folder_path = os.path.join(news_folder, folder)
        if os.path.isdir(folder_path):
            banner = os.path.join(folder, "banner.jpg")
            article_path = os.path.join(folder_path, "article.html")  # Update to use article.html
            if os.path.exists(article_path):
                with open(article_path, 'r') as file:
                    content = file.read()
                news.append({
                    'id': folder,  # unique ID for each news (folder name)
                    'title': folder.replace("_", " ").capitalize(),
                    'banner': banner,
                    'content': content
                })
    return news

@app.route('/news_images/<news_id>/<filename>')
def news_images(news_id, filename):
    return send_from_directory(os.path.join(app.root_path, 'news', news_id), filename)

# Home page route
@app.route('/')
def home():
    news_items = get_news()
    return render_template('home.html', news_items=news_items)

# Route to load specific news articles from the 'news' folder
@app.route('/news/<news_id>')
def news_article(news_id):
    news_folder = os.path.join(app.root_path, 'news', news_id)
    
    # Path to the article content
    article_file = os.path.join(news_folder, 'article.html')
    banner_file = os.path.join(news_folder, 'banner.jpg')

    # Check if the article file exists
    if not os.path.exists(article_file):
        return abort(404, description="News not found")

    # Read the content of the article (since it contains HTML tags)
    with open(article_file, 'r') as file:
        article_content = Markup(file.read())  # Markup allows safe rendering of HTML content

    # Pass the content and banner to the template
    return render_template('base_news.html', news_title=news_id.capitalize(), banner=banner_file, content=article_content)

# News overview page
@app.route('/news')
def news_overview():
    news_items = get_news()
    return render_template('news_overview.html', news_items=news_items)

if __name__ == '__main__':
    app.run(debug=True)
