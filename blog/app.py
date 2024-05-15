from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from models import User, BlogPost, db
from ai_module import process_user_query
import openai
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['POSTS_PER_PAGE'] = 10
db.init_app(app)
# Routes

@app.route('/')
def index():
    try:
        user = User.query.get(session.get('user_id'))
        return render_template('index.html', user=user)
    except Exception as e:
        flash('An error occurred while loading the page.', 'error')
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                session['user_id'] = user.id
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        return render_template('login.html')
    except Exception as e:
        flash('An error occurred during login.', 'error')
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')
    except Exception as e:
        flash('An error occurred during registration.', 'error')
        return render_template('register.html')

@app.route('/logout')
def logout():
    try:
        session.clear()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash('An error occurred during logout.', 'error')
        return redirect(url_for('index'))

@app.route('/generate_post', methods=['POST'])
def generate_post():
    try:
        user_id = session.get('user_id')

        if user_id is None:
            flash('User ID not found in session.', 'error')
            return redirect(url_for('index'))

        user = User.query.get(user_id)
        topic = request.form.get('topic')

        if not topic:
            flash('Topic is missing.', 'error')
            return redirect(url_for('index'))

        content = process_user_query(topic)

        if not content:
            flash('Failed to generate blog post content.', 'error')
            return redirect(url_for('index'))

        # Assuming BlogPost model has a 'content' field
        post = BlogPost(title=topic, content=content, author=user)
        db.session.add(post)
        db.session.commit()
        flash('Blog post generated successfully!', 'success')

        # Pass topic and content to blog.html template for display
        return render_template('blog.html', topic=topic, content=content, user=user)

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the database session to revert any changes
        flash('Database error occurred.', 'error')
        return redirect(url_for('index'))

    except KeyError:
        flash('User ID not found in session.', 'error')
        return redirect(url_for('index'))

    except Exception as e:
        flash('An error occurred while generating the blog post.', 'error')
        return redirect(url_for('index'))


@app.route('/history')
def history():
    try:
        if 'user_id' not in session:
            flash('You need to login to view history', 'error')
            return redirect(url_for('index'))

        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('index'))

        page = request.args.get('page', 1, type=int)
        posts = user.posts.paginate(page, app.config['POSTS_PER_PAGE'], False)

        if not posts.items:
            flash('No posts found', 'info')
            return redirect(url_for('index'))

        return render_template('history.html', posts=posts)
    except Exception as e:
        flash('An error occurred while loading the history page.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
