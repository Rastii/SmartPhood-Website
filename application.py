import flask
from flask import Flask, request, session, redirect, flash, json, \
    render_template, abort, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from hashlib import sha256 
import bcrypt
from functools import wraps

application = flask.Flask(__name__)
application.config.from_pyfile('application.cfg')
db = SQLAlchemy(application)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'auth' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login_page'))
    return decorated_function

def gen_api_key(username, salt):
    sha_hash = sha256()
    sha_hash.update(salt + ":" + username)
    return sha_hash.hexdigest()

@application.route('/', methods=['GET'])
@login_required
def index_page():
    return render_template('index.html', user=session['auth'])

@application.route('/login', methods=['GET'])
def login_page():
    if 'auth' in session:
        return redirect(url_for('index_page'))
    else:
        return render_template('login.html')


@application.route('/register', methods=['POST'])
def register_user():
    if all (x in request.form for x in ('username', 'password')):
        salt = bcrypt.gensalt()
        password = bcrypt.hashpw(request.form['password'], salt)
        query = '''
            INSERT INTO users VALUES(NULL, :username, :salt, :hash);
        '''
        try:
            result = db.session.execute(query, {
                'username': request.form['username'],
                'salt': salt,
                'hash': password
            })
            u_id = result.lastrowid
            key = gen_api_key(request.form['username'], salt)
            query = '''
                INSERT INTO api_keys VALUES (NULL, :u_id, :key)
            '''
            result2 = db.session.execute(query, {
                'u_id': u_id,
                'key': key
            })
            db.session.commit()
            session['auth'] = request.form['username']
            return '1'
        except:
            return '-1' #error in the query... (user exists)
    else:
        return '0' #missing post variables!

@application.route('/login', methods=['POST'])
def login_user():
    if all (x in request.form for x in ('username', 'password')):
        query = '''
            SELECT salt, password FROM users WHERE username=:username
        '''
        try:
            tupl = db.session.execute(query, {
                'username':request.form['username']
            }).first()
            salt, password = tupl
            print 'retrieved salt: ' + salt
            print 'retrieved hash: ' + password
            if(bcrypt.hashpw(request.form['password'], salt) == password):
                session['auth'] = request.form['username']
                return '1'
            else:
                return '0'
        except:
            return '0'
    else:
        return '-1'

@application.route('/logout', methods=['GET'])
def logout():
    if 'auth' in session:
        session.pop('auth', None)
    return redirect(url_for('login_page'))

@application.route('/mobile/login', methods=['POST'])
def login_mobile_user():
    if all (x in request.form for x in ('username', 'password')):
        query = '''
            SELECT K.key, U.salt, U.password FROM users U, api_keys K 
            WHERE U.username=:username AND U.id=K.u_id;
        '''
        try:
            tupl = db.session.execute(query, {
                'username':request.form['username']
            }).first()
            if tupl:
                key, salt, password = tupl
                if(bcrypt.hashpw(request.form['password'], salt) == password):
                    return key
                else:
                    #badpass
                    return '0'
            else:
                #No username exists
                return '0'
        except:
            #Error with the SQL requests
            return '-1'
    else:
        #All post variables do not exist
        return '-1'

@application.route('/api/recipes', methods=['GET'])
@login_required
def get_recipes():
    data = []
    query = '''
        SELECT * FROM recipes
    '''
    try:
        recipes = db.session.execute(query)
        for _id, name, instructions, author in recipes:
            data.append({
                'id': _id,
                'name': name,
                'instructions': instructions,
                'author': author
            })
        return json.dumps(data)
    except:
        return '-1'


@application.route('/api/recipes/<ingredient>', methods=['GET'])
@login_required
def get_recipes_by_ingredient(ingredient):
    data = []
    query = '''
        SELECT R.*
        FROM recipes R, ingredients I
        WHERE R.id=I.r_id AND I.name LIKE :ingredient
    '''
    try:
        recipes = db.session.execute(query, {
            'ingredient': '%'+ingredient+'%'   
        })
        for _id, name, instructions, author in recipes:
            data.append({
                'id': _id,
                'name': name,
                'instructions': instructions,
                'author': author
            })
        return json.dumps(data)
    except:
        return '-1'

def create_recipe(username, data):
    query = '''
        INSERT INTO recipes 
        VALUES(NULL, :name, :instructions, :author)
    '''
    query2 = '''
        INSERT INTO ingredients
        VALUES(NULL, :r_id, :name, :calories, :amount)
    '''
    try:
        for recipe in data:
            result = db.session.execute(query, {
                'name': recipe['name'],
                'instructions': recipe['instruction'],
                'author': username
            })
            db.session.commit()
            r_id = result.lastrowid
            for ingredient in recipe['ingredients']:
                result2 = db.session.execute(query2, {
                    'r_id': r_id,
                    'name': ingredient['name'],
                    'calories': ingredient['calories'],
                    'amount': ingredient['amount']
                })
                db.session.commit()
        return 1
    except:
        return -1


@application.route('/api/recipes', methods=['POST'])
def upload_recipes():
    if 'key' in request.args:
        query = '''
            SELECT U.username
            FROM users U, api_keys K
            WHERE K.key=:key AND K.u_id=U.id
        '''
        data = json.loads(request.data)
        try:
            result = db.session.execute(query, {
                'key': request.args['key']
            }).first()
            if result:
                username = result.username
                if create_recipe(username, data):
                    return '1'
                else: 
                    return '-1'
            else:
                abort(401)
        except:
            return '-1'
    else:
        abort(401)

@application.route('/api/ingredients/<recipe_id>')
@login_required
def get_recipe_ingredients(recipe_id):
    data = []
    query = '''
        SELECT I.name, I.amount
        FROM ingredients I, recipes R
        WHERE I.r_id=:recipe_id AND I.r_id=R.id
        ORDER BY I.name ASC
    '''
    try:
        ingredients = db.session.execute(query, {
            'recipe_id': recipe_id
        })
        for name, amount in ingredients:
            data.append({
                'name': name,
                'amount': amount
            })
        return json.dumps(data)
    except:
        return '-1'

@application.route('/api/<search_term>', methods=['GET'])
def get_ingredients(search_term):
    data = []
    query = '''
        SELECT name, calories 
        FROM search_ingredients 
        WHERE name LIKE :term
        ORDER BY name ASC
    '''
    try:
        projects = db.session.execute(query, {
            'term': '%' + search_term + '%'
        })
        for name, calories in projects:
            data.append({
                'name': name,
                'calories': calories
            })
        return json.dumps(data)
    except:
        return '-1'
 
if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
