from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import jwt
from werkzeug.utils import secure_filename

MONGODB_CONNECTION_STRING = "mongodb+srv://kentang:eUenw9z4QIlEoGzW@cluster0.mjce1r3.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.lexiarchiver

app = Flask(__name__)
SECRET_KEY = "7kU3kX2ijYQkzi4B"

@app.route("/dashboard")
def dashboard():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive,
            SECRET_KEY,
            algorithms=['HS256']
        )
        print(token_receive)
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('dashboard.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem a logging you in'
        return redirect(url_for('login', msg=msg))
    

@app.route("/login", methods=['GET'])
def login():
    msg = request.args.get('msg')
    return render_template('login.html', msg=msg)

@app.route("/sign_in",methods=['POST'])
def sign_in():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": username_receive,
            # the token will be valid for 24 hours
            "exp": datetime.utcnow() + timedelta(seconds=60*60*24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )
    # Let's also handle the case where the id and
    # password combination cannot be found
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "Invalid username or password. Please try again.",
            }
        )


@app.route("/update_profile", methods=['POST'])
def update_profile():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload['id']
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        city = request.form.get('city')
        bio = request.form.get('bio')
        email = request.form.get('email')
        phone = request.form.get('nophone')
        
        new_doc = {
            'first_name': first_name,
            'last_name': last_name,
            'city': city,
            'bio': bio,
            'email': email,
            'nophone': phone
        }
        
        if 'file_give' in request.files:
            file = request.files['file_give']
            filename = secure_filename(file.filename)
            extension = filename.split('.')[-1]
            file_path = f'profile_pics/{username}.{extension}'
            file.save('./static/' + file_path)
            new_doc['profile_pic'] = filename
            new_doc['profile_pic_real'] = file_path
        
        db.users.update_one({'username': payload['id']}, {'$set': new_doc})
        return jsonify({'result': 'success', 'msg': 'Profile updated!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5008, debug=True)