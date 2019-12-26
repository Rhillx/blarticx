from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
# from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.config.from_object('config.Config')

#init MYSQL
mysql = MySQL(app)

# Articles = Articles()

#Decorator to check if user logged_in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def index():
    
    return render_template('home.html')

@app.route('/about')
def ab():
    return render_template('about.html')



@app.route('/articles')
@ is_logged_in
def articles():

     #Create curson
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)

    

    # CLose connection
    cur.close()


@app.route('/article/<string:id>/')
def article(id):
    #Create curson
    cur = mysql.connection.cursor()

    #Get articles
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message = 'Passwords do not match')

    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.hash(str(form.password.data))


        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are registered!', 'Congrats')

        return redirect(url_for('index'))
    return  render_template('register.html', form=form )


#User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor

        cur = mysql.connection.cursor()

        #Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #Get stored hash
            data = cur.fetchone()
            password = data['password']

            #Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #passsed
                session['logged_in'] = True
                session['username'] = username

                flash('You are logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error = error)

            # CLose connectrion
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error = error)

    return render_template('login.html')  


#Logout 
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out!', 'success')

    return redirect(url_for('login'))
    

@app.route('/dashboard')
@ is_logged_in
def dashboard():
    #Create curson
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    # CLose connection
    cur.close()


    return render_template('dashboard.html')


#Create article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=5, max=100)])
    body = TextAreaField('Body', [validators.Length(min=30)])

 #Create add article route
@app.route('/add_article', methods = ['GET', 'POST'])
@ is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit
        mysql.connection.commit()

        # Close 
        cur.close()

        flash('Your article has been created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form = form)


@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    form = ArticleForm(request.form)

    # Create curson
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    form.title.data = article['title']
    form.body.data = article['body']



    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, id))

        # Commit
        mysql.connection.commit()

        # Close
        cur.close()

        flash('Your article has been updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/delete_article/<string:id>/', methods = ['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Your article had been deleted', 'success')

    return redirect(url_for('dashboard'))







if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
