import flask
from flask import Flask, request, session, redirect, flash, json, \
    render_template, abort, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from hashlib import sha256 
import bcrypt

application = flask.Flask(__name__)
application.config.from_pyfile('application.cfg')
db = SQLAlchemy(application)

def gen_api_key(username, salt):
    sha_hash = sha256()
    sha_hash.update(salt + ":" + username)
    return sha_hash.hexdigest()

@application.route('/')
def hello_world():
    return "Hello world!"


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
                return '1'
            else:
                return '0'
        except:
            return '0'
    else:
        return '-1'
    
@application.route('/api/<search_term>', methods=['GET'])
def get_ingredients(search_term):
    data = []
    query = '''
        SELECT name, calories FROM ingredients WHERE name LIKE :term
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
