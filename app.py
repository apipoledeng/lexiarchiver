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
        print(user_info)
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


@app.route("/add/inbox", methods=['GET'])
def add_inbox():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        return render_template('addsuratmasuk.html',user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))


@app.route("/add/inbox/save", methods=['POST'])
def add_inbox_save():
    print('Masuk')
    print(request.form)
    print(request.files)
    # return redirect(url_for('add_inbox'))
    # print(request.form["nama_surat_give"])
    # print(request.form["kategori_give"])
    # print(request.form["tanggal_give"])
    # print(request.form["pengirim_give"])
    # print(request.form["perihal_give"])
    # print(request.form["lampiran_give"])
    # print(request.form["keterangan_give"])
    nama_surat_receiver = request.form.get('nama_surat')
    kategori_receiver = request.form.get('kategori')
    tanggal_receiver = request.form.get('tanggal')
    pengirim_receiver = request.form.get('pengirim')
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')

    category = db.categories.find_one({'code':kategori_receiver})
    surat = {
        'nama_surat':nama_surat_receiver,
        'kategori_id': category['_id'],
        'tanggal':tanggal_receiver,
        'pengirim':pengirim_receiver,
        'keterangan':keterangan_receiver
    }
    if request.files != '':
        filename = secure_filename(lampiran_receiver.filename) #secure file
        extension = filename.split(".")[-1] #mengambil extension
        file_path = f"letters/{nama_surat_receiver}-{tanggal_receiver}.{extension}" #membuat path baru
        lampiran_receiver.save("./static/" + file_path) #menyimpan file
        surat["lampiran"] = './static/'+file_path #menambah key value
    db.letters.insert_one(surat)
    return redirect(url_for('list_surat_masuk', msg='The letter has been successfully saved.'))

@app.route("/list-surat-masuk")
def list_surat_masuk():
    return render_template('listsuratmasuk.html')

@app.route("/list-surat-keluar")
def list_surat_keluar():
    return render_template('listsuratkeluar.html')

@app.route("/list-surat-pemberitahuan")
def list_surat_pemberitahuan():
    return render_template('listpemberitahuan.html')

@app.route("/list-surat-pengumuman")
def list_surat_pengumuman():
    return render_template('listpengumuman.html')

@app.route("/editsuratmasuk")
def edit_surat_masuk():
    return render_template('editsuratmasuk.html')

@app.route("/edit-profile")
def edit_profile():
    return render_template('profil-modify1.html')

@app.route("/add-surat")
def add_surat():
    return render_template('addsuratmasuk.html')

if __name__ == '__main__':
    app.run('0.0.0.0', port=5008, debug=True)