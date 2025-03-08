from datetime import date
from dotenv import load_dotenv
import os

from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort, session, jsonify  # add session import if not already imported
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields import DateField, TimeField, SelectField
from markupsafe import Markup
import json
import shutil
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from PIL import Image  # new import
import secrets  # for secure state generation
from flask_wtf.file import FileField  # already imported? if not, add this
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
# from email_utils import *
import msal  # added import for Microsoft authentication

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Configure SQLAlchemy for reservations database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Define the base directory

# Define the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Add Microsoft OAuth configuration
app.config["MS_CLIENT_ID"] = "96fca20e-7d9c-4002-8e14-c8716b69ef90"
# with the environment variable value:
app.config["MS_CLIENT_SECRET"] = os.getenv("MS_CLIENT_SECRET")
app.config["MS_TENANT_ID"] = "e9c554b7-2aec-4238-9b8e-372753d596ae"
app.config["MS_AUTHORITY"] = "https://login.microsoftonline.com/" + app.config["MS_TENANT_ID"]
app.config["MS_REDIRECT_PATH"] = "/user/authorized"  # Must match the registered redirect URI
app.config["MS_SCOPE"] = ["User.Read"]

# Helper functions for MSAL
def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app.config["MS_CLIENT_ID"],
        authority=authority or app.config["MS_AUTHORITY"],
        client_credential=app.config["MS_CLIENT_SECRET"],
        token_cache=cache
    )

def _build_auth_url():
    msal_app = _build_msal_app()
    return msal_app.get_authorization_request_url(
        scopes=app.config["MS_SCOPE"],
        redirect_uri=url_for("authorized", _external=True)
    )

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
    filter_room = SelectField('Select Room', choices=[
        ('ALL', 'All Rooms'),
        ('study_room_b1', 'Study Room B1'),
        ('study_room_b2', 'Study Room B2'),
        ('study_room_b3', 'Study Room B3'),
        ('kitchen', 'Kitchen')
    ], validators=[DataRequired()])
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

# --- CHANGE in reservations route ---
@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    filter_form = FilterForm(request.args)
    reservation_form = ReservationForm()

    # If user hasn't chosen a date or room yet, set defaults
    from datetime import date, datetime, time
    if not filter_form.filter_date.data:
        filter_form.filter_date.data = date.today()
    if not filter_form.filter_room.data:
        filter_form.filter_room.data = 'ALL'

    selected_date = filter_form.filter_date.data.strftime('%Y-%m-%d')
    selected_room = filter_form.filter_room.data
    start_dt = datetime.combine(filter_form.filter_date.data, time.min)
    end_dt   = datetime.combine(filter_form.filter_date.data, time.max)

    # If "ALL", then fetch all reservations for that day; otherwise filter by a single room
    if selected_room == 'ALL':
        reservations_list = Reservation.query.filter(
            Reservation.start_time >= start_dt,
            Reservation.start_time <= end_dt
        ).order_by(Reservation.start_time).all()
    else:
        reservations_list = Reservation.query.filter(
            Reservation.room == selected_room,
            Reservation.start_time >= start_dt,
            Reservation.start_time <= end_dt
        ).order_by(Reservation.start_time).all()

    # Handle new reservation submission with date validation
    if request.method == 'POST' and reservation_form.validate_on_submit():
        if reservation_form.reservation_date.data < date.today():
            flash("Reservation date cannot be before today's date.", "danger")
            return redirect(url_for('reservations'))
        res_date = reservation_form.reservation_date.data
        start_dt_new = datetime.combine(res_date, reservation_form.start_time.data)
        end_dt_new   = datetime.combine(res_date, reservation_form.end_time.data)

        # Add error handling for unnatural times
        if start_dt_new >= end_dt_new:
            flash("End time must be after the start time.", "danger")
            return redirect(url_for('reservations'))

        # Check for overlapping reservation conflict
        conflict = Reservation.query.filter(
            Reservation.room == reservation_form.room.data,
            Reservation.start_time < end_dt_new,
            Reservation.end_time > start_dt_new
        ).first()
        if conflict:
            flash('The selected time slot is already reserved. Please choose a different time.', 'danger')
            return redirect(url_for('reservations'))
        else:
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
@app.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
def delete_reservation2(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash('Reservation deleted successfully!', 'success')
    return redirect(url_for('reservations'))


# Add new route to update reservation without requiring admin login
@app.route('/update_reservation/<int:reservation_id>', methods=['POST'])
def update_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    data = request.get_json()
    # Expected data: start_time, end_time, purpose, room, name, and date (YYYY-MM-DD)
    try:
        res_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        new_start = datetime.combine(res_date, datetime.strptime(data.get('start_time'), '%H:%M').time())
        new_end   = datetime.combine(res_date, datetime.strptime(data.get('end_time'), '%H:%M').time())
    except Exception as e:
        return jsonify({'error': 'Invalid date/time format'}), 400

    # Update fields
    reservation.name = data.get('name')
    reservation.purpose = data.get('purpose')
    reservation.room = data.get('room')
    reservation.start_time = new_start
    reservation.end_time = new_end

    # Optional: Add conflict checking here

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Update failed'}), 500

# New SQLAlchemy models for inventory system
class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    picture = db.Column(db.String(200))  # path to image

    def __repr__(self):
        return f"<InventoryItem {self.name}>"

class InventoryRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    requested_amount = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.String(200))
    return_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending/approved/rejected

# New WTForms
class InventoryRequestForm(FlaskForm):
    email = StringField('Your Email', validators=[DataRequired()])
    item = SelectField('Item', choices=[], validators=[DataRequired()])
    requested_amount = StringField('Amount', validators=[DataRequired()])
    purpose = TextAreaField('Purpose', validators=[DataRequired()])
    return_date = DateField('Return Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Request Item')

class InventoryItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    amount = StringField('Amount', validators=[DataRequired()])
    description = TextAreaField('Description')
    picture = FileField('Item Picture', validators=[])  # admin only upload
    submit = SubmitField('Save Item')

# New model for normal users (inventory users)
class InventoryUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# New WTForms for user login/registration
class UserLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])  # Use PasswordField in production
    submit = SubmitField('Login')

class UserRegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

# New routes for user registration, login, and logout
@app.route("/user/microsoft_login")
def microsoft_login():
    auth_url = _build_auth_url()
    return redirect(auth_url)

@app.route("/user/authorized")
def authorized():
    if "code" not in request.args:
        flash("Authorization failed.", "error")
        return redirect(url_for("user_login"))
    cache = msal.SerializableTokenCache()
    msal_app = _build_msal_app(cache=cache)
    result = msal_app.acquire_token_by_authorization_code(
        request.args["code"],
        scopes=app.config["MS_SCOPE"],
        redirect_uri=url_for("authorized", _external=True)
    )
    if "error" in result:
        flash("Login failed: " + result.get("error_description", ""), "error")
        return redirect(url_for("user_login"))
    session["inventory_user"] = result["id_token_claims"].get("email") or result["id_token_claims"].get("preferred_username")
    flash("Logged in successfully via Microsoft.", "success")
    return redirect(url_for("inventory"))

@app.route("/user/ms_logout")
def ms_logout():
    # Clear only the local session without redirecting to Microsoft's logout URL, then redirect to home
    session.clear()
    return redirect(url_for("home"))

# Modify existing user login route to use Microsoft SSO
@app.route('/user/login', methods=['GET'])
def user_login():
    return redirect(url_for("microsoft_login"))

# Optionally disable the registration route since Microsoft SSO is used
# @app.route('/user/register', methods=['GET', 'POST'])
# def user_register():
#     # ...existing registration code (disabled)...
#     pass

# Modify existing /inventory route to require user login
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if 'inventory_user' not in session:
        flash("Please login to make a request", "error")
        return redirect(url_for('user_login'))

    form = InventoryRequestForm()
    form.email.data = session['inventory_user']
    items = InventoryItem.query.all()
    form.item.choices = [(item.name, item.name) for item in items]

    if 'item' in request.args:
        form.item.data = request.args.get('item')

    if form.validate_on_submit():
        new_req = InventoryRequest(
            email=session['inventory_user'],
            item_name=form.item.data,
            requested_amount=int(form.requested_amount.data),
            purpose=form.purpose.data,
            return_date=form.return_date.data,
            status='pending'
        )
        db.session.add(new_req)
        db.session.commit()
        flash('Your request has been submitted and is pending approval.', 'success')
        return redirect(url_for('inventory'))

    today_date = date.today()  # Get today's date

    user_requests = InventoryRequest.query.filter_by(email=session['inventory_user']).all()
    borrowed_counts = {}
    for item in items:
        approved_reqs = InventoryRequest.query.filter(
            InventoryRequest.item_name == item.name,
            InventoryRequest.status == 'approved',
            InventoryRequest.return_date >= today_date
        ).all()
        borrowed_counts[item.id] = sum(req.requested_amount for req in approved_reqs)

    return render_template('inventory.html',
                           form=form,
                           items=items,
                           borrowed_counts=borrowed_counts,
                           user_requests=user_requests,
                           today=today_date)  # Pass today's date to the template

# New route: Allow a signed‐in user to return an item.
@app.route('/user/return_request/<int:req_id>', methods=['POST'])
def return_request(req_id):
    if 'inventory_user' not in session:
        flash("Please login", "error")
        return redirect(url_for('user_login'))
    user_email = session['inventory_user']
    req_item = InventoryRequest.query.get_or_404(req_id)
    if req_item.email != user_email:
        flash("Not authorized", "error")
        return redirect(url_for('inventory'))
    req_item.status = 'returned'
    db.session.commit()
    flash("Item returned successfully", "success")
    return redirect(url_for('inventory'))

# Modify admin_inventory route to check for unique item name
@app.route('/admin/inventory', methods=['GET', 'POST'])
@login_required
def admin_inventory():
    form = InventoryItemForm()
    if form.validate_on_submit():
        # Check if an item with the same name already exists
        existing = InventoryItem.query.filter_by(name=form.name.data.strip()).first()
        if existing:
            flash('Error: An inventory item with this name already exists.', 'error')
            return redirect(url_for('admin_inventory'))
        filename = None
        if form.picture.data:
            filename = secure_filename(form.picture.data.filename)
            inv_folder = os.path.join(BASE_DIR, 'static', 'inventory')
            if not os.path.exists(inv_folder):
                os.makedirs(inv_folder)
            picture_path = os.path.join(inv_folder, filename)
            form.picture.data.save(picture_path)
        new_item = InventoryItem(
            name=form.name.data.strip(),
            amount=int(form.amount.data),
            description=form.description.data,
            picture=filename
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('admin_inventory'))
    items = InventoryItem.query.all()
    # Initialize borrowed_counts as 0 for each existing inventory item
    borrowed_counts = { item.id: 0 for item in items }
    return render_template('edit_inventory.html', form=form, items=items, borrowed_counts=borrowed_counts)

# New route: admin review inventory requests
@app.route('/admin/inventory_requests', methods=['GET', 'POST'])
@login_required
def admin_inventory_requests():
    requests_list = InventoryRequest.query.order_by(InventoryRequest.id.desc()).all()
    req_id = request.args.get('id')
    action = request.args.get('action')
    if req_id and action:
        inv_req = InventoryRequest.query.get_or_404(req_id)
        item = InventoryItem.query.filter_by(name=inv_req.item_name).first()

        if action == 'approve':
            # Check if approving this request exceeds available items
            approved_reqs = InventoryRequest.query.filter(
                InventoryRequest.item_name == inv_req.item_name,
                InventoryRequest.status == 'approved'
            ).all()
            borrowed_count = sum(req.requested_amount for req in approved_reqs)

            if borrowed_count + inv_req.requested_amount > item.amount:
                flash("Cannot approve: Borrowed amount exceeds available inventory.", "danger")
                return redirect(url_for('admin_inventory_requests'))

            inv_req.status = 'approved'
            subject = "Your inventory request was approved!"
            body = f"Hello,\n\nYour request for '{inv_req.item_name}' has been approved."

        elif action == 'reject':
            inv_req.status = 'rejected'
            subject = "Your inventory request was rejected"
            body = f"Hello,\n\nYour request for '{inv_req.item_name}' has been rejected."

        db.session.commit()
        return redirect(url_for('admin_inventory_requests'))

    return render_template('inventory_requests.html', requests=requests_list)

# New route: Edit an existing inventory item (admin only)
@app.route('/admin/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    form = InventoryItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.amount = int(form.amount.data)
        item.description = form.description.data
        if form.picture.data:
            filename = secure_filename(form.picture.data.filename)
            inv_folder = os.path.join(BASE_DIR, 'static', 'inventory')
            if not os.path.exists(inv_folder):
                os.makedirs(inv_folder)
            picture_path = os.path.join(inv_folder, filename)
            form.picture.data.save(picture_path)
            item.picture = filename
        db.session.commit()
        flash('Inventory item updated successfully.', 'success')
        return redirect(url_for('admin_inventory'))
    return render_template('edit_inventory_item.html', form=form, item=item)

# Optional route: Delete an inventory item (admin only)
@app.route('/admin/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Inventory item deleted.', 'success')
    return redirect(url_for('admin_inventory'))

# Create database tables if they don't exist
with app.app_context():
    # init_mail(app)
    db.create_all()

@app.template_filter('escapejs')
def escapejs_filter(s):
    import json
    if not isinstance(s, str):
        s = str(s)
    # json.dumps returns a quoted string; remove outer quotes.
    return json.dumps(s)[1:-1]

# New route: Allow a signed-in user to cancel a pending request.
@app.route('/user/cancel_request/<int:req_id>', methods=['POST'], endpoint='cancel_request')
def cancel_request(req_id):
    if 'inventory_user' not in session:
        flash("Please login", "error")
        return redirect(url_for('user_login'))
    user_email = session['inventory_user']
    req_item = InventoryRequest.query.get_or_404(req_id)
    if req_item.email != user_email:
        flash("Not authorized", "error")
        return redirect(url_for('inventory'))
    if req_item.status != 'pending':
        flash("Only pending requests can be cancelled", "error")
        return redirect(url_for('inventory'))
    db.session.delete(req_item)
    db.session.commit()
    flash("Request cancelled successfully", "success")
    return redirect(url_for('inventory'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
