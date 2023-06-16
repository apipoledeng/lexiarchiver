from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import jwt
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

MONGODB_CONNECTION_STRING = "mongodb+srv://kentang:eUenw9z4QIlEoGzW@cluster0.mjce1r3.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.lexiarchiver

app = Flask(__name__)
SECRET_KEY = "7kU3kX2ijYQkzi4B"
app.secret_key=SECRET_KEY

ALLOWED_FILE = ['docx','doc', 'pdf']


# def get_file_size(file_path):
#     # Check if the file exists
#     if os.path.exists(file_path):
#         # Get the file size in bytes
#         file_size = os.path.getsize(file_path)
#         return file_size
#     else:
#         return None


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

@app.route("/list-surat-masuk")
def list_surat_masuk():
    list_surat = db.letters.find({'kategori':'SM'})
    jumlah_surat = db.letters.count_documents({'kategori':'SM'})
    return render_template('listsuratmasuk.html', list_surat=list_surat, jumlah_surat=jumlah_surat)

@app.route("/add-surat-masuk", methods=['GET'])
def add_surat_masuk():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        return render_template('addsuratmasuk.html',user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))


@app.route("/add-surat-masuk-save", methods=['POST'])
def add_surat_masuk_save():

    print('Masuk')
    print(request.form)
    print(request.files)
    nomor_surat_receiver = request.form.get('nomor_surat')
    kategori_receiver = request.form.get('kategori')
    pengirim_receiver = request.form.get('pengirim')
    tanggal_receiver = request.form.get('tanggal')
    tujuan_receiver = request.form['tujuan']
    perihal_receiver = request.form['perihal']
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')


    #ambil path dari file
    path_surat = ''
    #cek ukuan file
    ukuran_surat = os.path.getsize(lampiran_receiver.filename)
    print(ukuran_surat)
    print(type(ukuran_surat))
    #ambil extention surat
    filename = secure_filename(lampiran_receiver.filename)
    extension_surat = filename.split(".")[-1]
    #jika file extension in Allowed_file
    if extension_surat in ALLOWED_FILE:
        #lanjutkan proses
        #jika ukuran file < 5 Mb
        if ukuran_surat < 5242880:
            #lanjutkan proses
            tanggal_to_datetime = datetime.strptime(tanggal_receiver, "%Y-%m-%d")
            datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
            print(tanggal_to_datetime)
            print(datetime_to_tanggal)
            surat = {
                'nomor_surat':f'{kategori_receiver}/{nomor_surat_receiver}',
                'kategori': kategori_receiver,
                'tanggal':datetime_to_tanggal,
                'tujuan': tujuan_receiver,
                'perihal': perihal_receiver,
                'pengirim':pengirim_receiver,
                'keterangan':keterangan_receiver
            }
            if request.files != '':
                filename = secure_filename(lampiran_receiver.filename) #secure file
                extension = filename.split(".")[-1] #mengambil extension
                file_path = f"letters/{perihal_receiver}-{datetime_to_tanggal}.{extension}" #membuat path baru
                lampiran_receiver.save("./static/" + file_path) #menyimpan file
                surat["lampiran"] = file_path #menambah key value
            db.letters.insert_one(surat)
            flash('The letter has been successfully saved.', 'success')
            return redirect(url_for('list_surat_masuk'))
        else:
            #kirim alert message bahwa file melebihi batas
            flash('The file size exceeds 5 Mb.', 'error')
            return redirect(url_for('list_surat_masuk'))
    #jika tidak
    else:
        #kirim pesan "Pastikan file yang anda kirim memiliki extensi .docs atau pdf"
        flash('Make sure the file you send has the docx, doc or pdf extension', 'error')
        return redirect(url_for('list_surat_masuk'))


@app.route("/test", methods=['GET','POST'])
def test():
    if request.method=='POST':
        file = request.files['fileku']
        file_size = os.path.getsize(file.filename)
        if file_size > 1024 * 1024:  # 1MB
            return 'File size exceeds the limit.'
        # flash('error:This is an error message')
    return render_template('test.html')

@app.route("/surat-masuk/delete/<id>", methods=['GET'])
def surat_masuk_delete(id):
    db.letters.delete_one({'_id':ObjectId(id)})
    flash('The letter has been successfully deleted.','success')
    return redirect(url_for('list_surat_masuk'))

@app.route("/surat-masuk/update/<id>", methods=['GET','POST'])
def surat_masuk_update(id):
    obj = db.letters.find_one({'_id':ObjectId(id)})
    print(obj)
    if request.method == 'POST':
        print("Ngepost")
        tanggal_to_datetime = datetime.strptime(request.form['tanggal'], "%Y-%m-%d")
        datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
        lampiran_receiver =request.files['lampiran']
        if request.files != '':
            filename = secure_filename(lampiran_receiver.filename) #secure file
            extension = filename.split(".")[-1] #mengambil extension
            file_path = f"letters/{request.form['perihal']}-{datetime_to_tanggal}.{extension}" #membuat path baru
            lampiran_receiver.save("./static/" + file_path) #menyimpan file
        else:
            file_path=''
        data = {
            'nomor_surat':f"SM/{request.form['nomor_surat']}",
            'kategori':request.form['kategori'],
            'tanggal':datetime_to_tanggal,
            'tujuan':request.form['tujuan'],
            'perihal':request.form['perihal'],
            'pengirim':request.form['pengirim'],
            'keterangan':request.form['keterangan'],
            'lampiran':file_path
        }
        db.letters.update_one({'_id':ObjectId(id)},{'$set': data})
        flash('The letter has been successfully edited.','success')
        return redirect(url_for('list_surat_masuk'))
    obj['nomor_surat']=obj['nomor_surat'].replace("SM/",'')
    date_object = datetime.strptime(obj['tanggal'], '%d-%m-%Y')
    new_date_string = date_object.strftime('%Y-%m-%d')
    obj['tanggal'] = new_date_string
    print(obj['kategori'])
    return render_template('editsuratmasuk.html', surat=obj, id=id)


@app.route("/list-surat-keluar")
def list_surat_keluar():
    return render_template('listsuratkeluar.html')

@app.route("/list-surat-pemberitahuan")
def list_surat_pemberitahuan():
    return render_template('listpemberitahuan.html')

@app.route("/list-surat-pengumuman")
def list_surat_pengumuman():
    return render_template('listpengumuman.html')

@app.route("/editsurat")
def edit_surat():
    return render_template('editsurat.html')

@app.route("/edit-profile")
def edit_profile():
    return render_template('profil-modify1.html')

@app.route("/add-surat-keluar")
def add_surat_keluar():
    return render_template('addsuratkeluar.html')

if __name__ == '__main__':
    app.run('0.0.0.0', port=5008, debug=True)