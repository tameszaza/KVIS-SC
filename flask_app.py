from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields import DateField, TimeField, SelectField
from markupsafe import Markup
import os
import json
import shutil
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from PIL import Image  # new import

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Configure SQLAlchemy for reservations database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    snippet = StringField('Snippet', validators=[DataRequired()])
    content = TextAreaField('Content (HTML)', validators=[DataRequired()])
    banner = FileField('Banner Image')
    submit = SubmitField('Submit')

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Add new login route
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
# --- New Section: Reservation System ---

# SQLAlchemy Model for Reservations
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Reservation {self.id} for {self.room}>"

# WTForm for creating a new reservation
class ReservationForm(FlaskForm):
    reservation_date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    name = StringField('Your Name', validators=[DataRequired()])
    purpose = TextAreaField('Purpose', validators=[DataRequired()])
    room = SelectField('Room', choices=[('study_room_b1', 'Study Room B1'),
                                          ('study_room_b2', 'Study Room B2'),
                                          ('study_room_b3', 'Study Room B3'),
                                          ('kitchen', 'Kitchen')], validators=[DataRequired()])
    submit = SubmitField('Reserve')

# WTForm for filtering reservations (timeline view)
class FilterForm(FlaskForm):
    filter_date = DateField('Select Date', validators=[DataRequired()], format='%Y-%m-%d')
    filter_room = SelectField('Select Room', choices=[('study_room_b1', 'Study Room B1'),
                                                        ('study_room_b2', 'Study Room B2'),
                                                        ('study_room_b3', 'Study Room B3'),
                                                        ('kitchen', 'Kitchen')], validators=[DataRequired()])
    submit = SubmitField('Filter')

# --- End of Reservation System Section ---

# News and other functions (existing code)
def get_news():
    news_folder = os.path.join(BASE_DIR, "news")
    news = []
    if os.path.exists(news_folder):
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
    return send_from_directory(os.path.join(BASE_DIR, 'news', news_id), filename)

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
    news_folder = os.path.join(BASE_DIR, 'news', news_id)
    article_file = os.path.join(news_folder, 'article.html')
    metadata_file = os.path.join(news_folder, 'metadata.json')

    if not os.path.exists(article_file):
        return abort(404, description="News not found")

    with open(article_file, 'r') as file:
        full_content = file.read()

    paragraphs = full_content.split('</p>', 1)
    if len(paragraphs) > 1:
        intro_content = paragraphs[0] + '</p>'
        remaining_content = paragraphs[1]
    else:
        intro_content = full_content
        remaining_content = ''

    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        news_title = metadata.get('title', news_id.replace('_', ' ').title())
    else:
        news_title = news_id.replace('_', ' ').title()

    return render_template('base_news.html',
                           news_title=news_title,
                           intro_content=Markup(intro_content),
                           remaining_content=Markup(remaining_content),
                           news_id=news_id)

@app.route('/news')
def news_overview():
    news_items = get_news()
    return render_template('news_overview.html', news_items=news_items)

@app.route('/admin')
@login_required
def admin_dashboard():
    news_items = get_news()
    return render_template('admin_dashboard.html', news_items=news_items)

def compress_and_save_image(uploaded_file, high_path, low_path):
    image = Image.open(uploaded_file)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    # Resize if image width exceeds 1920px
    max_width = 1920
    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)
    # Save high quality image with quality set to 70
    image.save(high_path, format='JPEG', optimize=True, quality=70)
    # Save low quality image for overview with quality set to 30
    image.save(low_path, format='JPEG', optimize=True, quality=30)

@app.route('/admin/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        snippet = form.snippet.data.strip()
        content = form.content.data
        banner = form.banner.data

        news_id = title.lower().replace(' ', '_')
        news_folder = os.path.join(BASE_DIR, 'news', news_id)
        if not os.path.exists(news_folder):
            os.makedirs(news_folder)
        else:
            flash('A news article with this title already exists.')
            return redirect(url_for('add_news'))

        # Compress and save banner image if provided
        if banner:
            high_path = os.path.join(news_folder, 'banner.jpg')
            low_path  = os.path.join(news_folder, 'banner_low.jpg')
            compress_and_save_image(banner, high_path, low_path)

        article_path = os.path.join(news_folder, 'article.html')
        with open(article_path, 'w') as f:
            f.write(content)

        metadata = {'title': title, 'snippet': snippet}
        metadata_path = os.path.join(news_folder, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        flash('News article added successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_news.html', form=form)

@app.route('/admin/edit_news/<news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    news_folder = os.path.join(BASE_DIR, 'news', news_id)
    article_file = os.path.join(news_folder, 'article.html')
    metadata_file = os.path.join(news_folder, 'metadata.json')

    if not os.path.exists(news_folder):
        abort(404)

    with open(article_file, 'r') as f:
        content = f.read()
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    title = metadata.get('title', news_id.replace('_', ' ').title())
    snippet = metadata.get('snippet', '')

    form = NewsForm()
    if request.method == 'GET':
        form.title.data = title
        form.snippet.data = snippet
        form.content.data = content
    if form.validate_on_submit():
        new_title = form.title.data.strip()
        new_snippet = form.snippet.data.strip()
        new_news_id = new_title.lower().replace(' ', '_')
        new_news_folder = os.path.join(BASE_DIR, 'news', new_news_id)
        if new_news_id != news_id:
            os.rename(news_folder, new_news_folder)
            news_folder = new_news_folder
            news_id = new_news_id
            article_file = os.path.join(news_folder, 'article.html')
            metadata_file = os.path.join(news_folder, 'metadata.json')

        with open(article_file, 'w') as f:
            f.write(form.content.data)

        # Compress and update banner image if provided
        if form.banner.data:
            high_path = os.path.join(news_folder, 'banner.jpg')
            low_path  = os.path.join(news_folder, 'banner_low.jpg')
            compress_and_save_image(form.banner.data, high_path, low_path)

        metadata = {'title': new_title, 'snippet': new_snippet}
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

        flash('News article updated successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_news.html', form=form)

@app.route('/admin/delete_news/<news_id>', methods=['POST'])
@login_required
def delete_news(news_id):
    news_folder = os.path.join(BASE_DIR, 'news', news_id)
    if not os.path.exists(news_folder):
        abort(404)

    shutil.rmtree(news_folder)
    flash('News article deleted successfully!')
    return redirect(url_for('admin_dashboard'))

def load_progress_reports():
    progress_file = os.path.join(BASE_DIR, 'progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    else:
        return {'plan': [], 'doing': [], 'done': []}

def save_progress_reports(data):
    progress_file = os.path.join(BASE_DIR, 'progress.json')
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

# --- New Route: Room Reservation System ---
from datetime import date  # add this if not already imported

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    filter_form = FilterForm(request.args)
    reservation_form = ReservationForm()
    
    # Set default filter values if not provided
    if not filter_form.filter_date.data:
        filter_form.filter_date.data = date.today()
    if not filter_form.filter_room.data:
        filter_form.filter_room.data = 'study_room_b1'
    
    selected_date = filter_form.filter_date.data.strftime('%Y-%m-%d')
    selected_room = filter_form.filter_room.data
    start_dt = datetime.combine(filter_form.filter_date.data, time.min)
    end_dt = datetime.combine(filter_form.filter_date.data, time.max)
    reservations_list = Reservation.query.filter(
        Reservation.room == selected_room,
        Reservation.start_time >= start_dt,
        Reservation.start_time <= end_dt
    ).order_by(Reservation.start_time).all()
    
    # Handling new reservation submission remains unchanged
    # Modify the condition to remove an extra check for reservation_form.submit.data
    if request.method == 'POST' and reservation_form.validate_on_submit():
        res_date = reservation_form.reservation_date.data
        start_dt_new = datetime.combine(res_date, reservation_form.start_time.data)
        end_dt_new = datetime.combine(res_date, reservation_form.end_time.data)

        # Debug: print form submission details
        print("Debug: Reservation submission details:")
        print("Room:", reservation_form.room.data)
        print("Name:", reservation_form.name.data)
        print("Purpose:", reservation_form.purpose.data)
        print("Start time:", start_dt_new)
        print("End time:", end_dt_new)

        # Check for overlapping reservation conflict in the same room
        conflict = Reservation.query.filter(
            Reservation.room == reservation_form.room.data,
            Reservation.start_time < end_dt_new,
            Reservation.end_time > start_dt_new
        ).first()
        if conflict:
            print("Debug: Conflict found:", conflict)
            flash('The selected time slot is already reserved. Please choose a different time.', 'danger')
            return redirect(url_for('reservations'))
        else:
            print("Debug: No conflicting reservation found. Proceeding.")

        new_reservation = Reservation(
            room=reservation_form.room.data,
            name=reservation_form.name.data,
            purpose=reservation_form.purpose.data,
            start_time=start_dt_new,
            end_time=end_dt_new
        )
        db.session.add(new_reservation)
        db.session.commit()
        flash('Reservation created successfully!', 'success')
        return redirect(url_for('reservations'))

    
    return render_template('reservations.html',
                           filter_form=filter_form,
                           reservation_form=reservation_form,
                           reservations=reservations_list,
                           selected_date=selected_date,
                           selected_room=selected_room)

# --- New Routes: Reservation Timeline Management ---

@app.route('/admin/reservations')
@login_required
def manage_reservations():
    reservations_list = Reservation.query.order_by(Reservation.start_time).all()
    return render_template('edit_timeline.html', reservations=reservations_list)

@app.route('/admin/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationForm(obj=reservation)
    if form.validate_on_submit():
        # Update reservation details
        res_date = form.reservation_date.data
        reservation.room = form.room.data
        reservation.name = form.name.data
        reservation.purpose = form.purpose.data
        reservation.start_time = datetime.combine(res_date, form.start_time.data)
        reservation.end_time = datetime.combine(res_date, form.end_time.data)
        # Check for conflict excluding itself
        conflict = Reservation.query.filter(
            Reservation.id != reservation.id,
            Reservation.room == form.room.data,
            Reservation.start_time < reservation.end_time,
            Reservation.end_time > reservation.start_time
        ).first()
        if conflict:
            flash('The selected time slot conflicts with another reservation.', 'danger')
            return redirect(url_for('edit_reservation', reservation_id=reservation.id))
        db.session.commit()
        flash('Reservation updated successfully!', 'success')
        return redirect(url_for('manage_reservations'))
    # Prepopulate the date separately
    form.reservation_date.data = reservation.start_time.date()
    # ...existing code...
    return render_template('edit_reservation.html', form=form, reservation=reservation)

@app.route('/admin/delete_reservation/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted successfully!', 'success')
    return redirect(url_for('manage_reservations'))

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
