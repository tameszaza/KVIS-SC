from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from markupsafe import Markup
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Replace with real authentication
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':  # Replace with secure check
            user = User(id=username)
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

def get_news():
    news_folder = os.path.join(app.root_path, "news")
    news = []
    for folder in os.listdir(news_folder):
        folder_path = os.path.join(news_folder, folder)
        if os.path.isdir(folder_path):
            banner = os.path.join(folder, "banner.jpg")
            article_path = os.path.join(folder_path, "article.html")
            metadata_path = os.path.join(folder_path, 'metadata.json')
            if os.path.exists(article_path):
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    title = metadata.get('title', folder.replace('_', ' ').title())
                    snippet = metadata.get('snippet', '')
                else:
                    title = folder.replace('_', ' ').title()
                    snippet = ''
                news.append({
                    'id': folder,
                    'title': title,
                    'banner': banner,
                    'snippet': snippet,
                })
    return news



@app.route('/news_images/<news_id>/<filename>')
def news_images(news_id, filename):
    return send_from_directory(os.path.join(app.root_path, 'news', news_id), filename)

# Home page route
@app.route('/')
def home():
    news_items = get_news()
    progress_data = load_progress_reports()
    return render_template('home.html', news_items=news_items,
                           progress_plan=progress_data['plan'],
                           progress_doing=progress_data['doing'],
                           progress_done=progress_data['done'])

@app.route('/news/<news_id>')
def news_article(news_id):
    news_folder = os.path.join(app.root_path, 'news', news_id)
    article_file = os.path.join(news_folder, 'article.html')
    metadata_file = os.path.join(news_folder, 'metadata.json')

    if not os.path.exists(article_file):
        return abort(404, description="News not found")

    # Read the content of the article
    with open(article_file, 'r') as file:
        article_content = Markup(file.read())

    # Check for metadata.json
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        news_title = metadata.get('title', news_id.replace('_', ' ').title())
    else:
        news_title = news_id.replace('_', ' ').title()

    # Pass the content and banner to the template
    return render_template('base_news.html', news_title=news_title, content=article_content, news_id=news_id)


# News overview page
@app.route('/news')
def news_overview():
    news_items = get_news()
    return render_template('news_overview.html', news_items=news_items)

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    news_items = get_news()
    return render_template('admin_dashboard.html', news_items=news_items)

class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content (HTML)', validators=[DataRequired()])
    banner = FileField('Banner Image')  # Optional during editing
    submit = SubmitField('Submit')

@app.route('/admin/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        content = form.content.data
        banner = form.banner.data

        # Create a safe folder name
        news_id = title.lower().replace(' ', '_')
        news_folder = os.path.join(app.root_path, 'news', news_id)
        if not os.path.exists(news_folder):
            os.makedirs(news_folder)
        else:
            flash('A news article with this title already exists.')
            return redirect(url_for('add_news'))

        # Save the banner image
        banner_path = os.path.join(news_folder, 'banner.jpg')
        banner.save(banner_path)

        # Save the content
        article_path = os.path.join(news_folder, 'article.html')
        with open(article_path, 'w') as f:
            f.write(content)

        # Save metadata
        metadata = {'title': title}
        metadata_path = os.path.join(news_folder, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        flash('News article added successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_news.html', form=form)

@app.route('/admin/edit_news/<news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news_folder = os.path.join(app.root_path, 'news', news_id)
    article_file = os.path.join(news_folder, 'article.html')
    metadata_file = os.path.join(news_folder, 'metadata.json')

    if not os.path.exists(news_folder):
        abort(404)

    # Load existing data
    with open(article_file, 'r') as f:
        content = f.read()
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    title = metadata.get('title', news_id.replace('_', ' ').title())

    form = NewsForm()
    if request.method == 'GET':
        form.title.data = title
        form.content.data = content
    if form.validate_on_submit():
        # Update title (rename folder if title changes)
        new_title = form.title.data.strip()
        new_news_id = new_title.lower().replace(' ', '_')
        new_news_folder = os.path.join(app.root_path, 'news', new_news_id)
        if new_news_id != news_id:
            os.rename(news_folder, new_news_folder)
            news_folder = new_news_folder
            news_id = new_news_id
            article_file = os.path.join(news_folder, 'article.html')
            metadata_file = os.path.join(news_folder, 'metadata.json')

        # Update content
        with open(article_file, 'w') as f:
            f.write(form.content.data)

        # Update banner if a new one is uploaded
        if form.banner.data:
            banner_file = os.path.join(news_folder, 'banner.jpg')
            form.banner.data.save(banner_file)

        # Update metadata
        metadata = {'title': new_title}
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        flash('News article updated successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_news.html', form=form)

@app.route('/admin/delete_news/<news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news_folder = os.path.join(app.root_path, 'news', news_id)
    if not os.path.exists(news_folder):
        abort(404)

    # Delete the news folder and its contents
    import shutil
    shutil.rmtree(news_folder)

    flash('News article deleted successfully!')
    return redirect(url_for('admin_dashboard'))

# Progress Report Management
def load_progress_reports():
    progress_file = os.path.join(app.root_path, 'progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    else:
        return {'plan': [], 'doing': [], 'done': []}

def save_progress_reports(data):
    progress_file = os.path.join(app.root_path, 'progress.json')
    with open(progress_file, 'w') as f:
        json.dump(data, f)

class ProgressForm(FlaskForm):
    plan = TextAreaField('What We Plan to Do')
    doing = TextAreaField('What We Are Doing')
    done = TextAreaField('What We Have Done')
    submit = SubmitField('Update')

@app.route('/admin/progress', methods=['GET', 'POST'])
@login_required
def manage_progress():
    progress_data = load_progress_reports()
    form = ProgressForm()
    if form.validate_on_submit():
        progress_data['plan'] = form.plan.data.split('\n')
        progress_data['doing'] = form.doing.data.split('\n')
        progress_data['done'] = form.done.data.split('\n')
        save_progress_reports(progress_data)
        flash('Progress report updated successfully!')
        return redirect(url_for('admin_dashboard'))
    else:
        form.plan.data = '\n'.join(progress_data['plan'])
        form.doing.data = '\n'.join(progress_data['doing'])
        form.done.data = '\n'.join(progress_data['done'])
    return render_template('manage_progress.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
