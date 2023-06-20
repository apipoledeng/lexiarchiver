from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_file
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib
import jwt
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
import tempfile

MONGODB_CONNECTION_STRING = "mongodb+srv://kentang:eUenw9z4QIlEoGzW@cluster0.mjce1r3.mongodb.net/?retryWrites=true&w=majority"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.lexiarchiver

app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = './static/ngetes/'
SECRET_KEY = "7kU3kX2ijYQkzi4B"
app.secret_key=SECRET_KEY

ALLOWED_FILE = ['docx','doc', 'pdf']

@app.route("/")
def home():
    return render_template('home.html')


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
        jumlah_surat_masuk = db.letters.count_documents({'kategori':'SM'})
        jumlah_surat_keluar = db.letters.count_documents({'kategori':'SK'})
        jumlah_surat_pemberitahuan = db.letters.count_documents({'kategori':'SP'})
        jumlah_surat_pengumuman = db.letters.count_documents({'kategori':'SP'})
        data = [jumlah_surat_masuk, jumlah_surat_keluar, jumlah_surat_pemberitahuan,jumlah_surat_pengumuman]
        print(user_info)
        return render_template('dashboard.html', user_info=user_info, data=data)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        flash(msg,'error')
        return redirect(url_for('login'))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem a logging you in'
        flash(msg,'error')
        return redirect(url_for('login'))
    

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
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        list_surat = db.letters.find({'kategori':'SM'})
        jumlah_surat = db.letters.count_documents({'kategori':'SM'})
        return render_template('listsuratmasuk.html', list_surat=list_surat, jumlah_surat=jumlah_surat,user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))

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
    nomor_surat_receiver = request.form.get('nomor_surat')
    kategori_receiver = request.form.get('kategori')
    pengirim_receiver = request.form.get('pengirim')
    tanggal_receiver = request.form.get('tanggal')
    tujuan_receiver = request.form['tujuan']
    perihal_receiver = request.form['perihal']
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')


    #simpan file di tmp/foo
    lampiran_receiver.save('/tmp/foo')
    #akses dan cek ukuran file pada tmp/foo dir
    file_size = os.stat('/tmp/foo').st_size
    extension_surat = lampiran_receiver.filename.split(".")[-1]
    #cek ukuan file
    if file_size <= 5*1000*1000:
        #cek extensi
        if extension_surat not in ALLOWED_FILE:
            flash('The file must be .docs, .doc, and .pdf ', 'error')
            return redirect(url_for('list_surat_masuk'))
        #simpan surat
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
        print(lampiran_receiver)
        filename = secure_filename(lampiran_receiver.filename) #secure file
        file_path = f"letters/{kategori_receiver}_{nomor_surat_receiver}_{datetime_to_tanggal}_{filename}" #membuat path baru
        lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
        surat["lampiran"] = file_path #menambah key value
        db.letters.insert_one(surat)
        flash('The letter has been successfully saved.', 'success')
        return redirect(url_for('list_surat_masuk'))
    else:
        flash('The file size exceeds 5 Mb.', 'error')
        return redirect(url_for('list_surat_masuk'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE

@app.route("/surat-masuk/delete/<id>", methods=['GET'])
def surat_masuk_delete(id):
    db.letters.delete_one({'_id':ObjectId(id)})
    flash('The letter has been successfully deleted.','success')
    return redirect(url_for('list_surat_masuk'))

@app.route("/surat-masuk/update/<id>", methods=['GET','POST'])
def surat_masuk_update(id):
    obj = db.letters.find_one({'_id':ObjectId(id)})
    # print(obj)
    if request.method == 'POST':
        # print("Ngepost")
        tanggal_to_datetime = datetime.strptime(request.form['tanggal'], "%Y-%m-%d")
        datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
        lampiran_receiver =request.files['lampiran']
        
        lampiran_receiver.save('/tmp/foo')
        file_size = os.stat('/tmp/foo').st_size
        extension_surat = lampiran_receiver.filename.split(".")[-1]

        if file_size <= 5*1000*1000:
            #cek extensi
            if extension_surat not in ALLOWED_FILE:
                flash('The file must be .docs, .doc, and .pdf ', 'error')
                return redirect(url_for('list_surat_masuk'))
            filename = secure_filename(lampiran_receiver.filename) #secure file
            file_path = f"letters/{request.form['kategori']}_{request.form['nomor_surat']}_{datetime_to_tanggal}_{filename}" #membuat path baru            
            lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file    
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
        else:
            flash('The file size exceeds 5 Mb.', 'error')
            return redirect(url_for('list_surat_masuk'))
    obj['nomor_surat']=obj['nomor_surat'].replace("SM/",'')
    date_object = datetime.strptime(obj['tanggal'], '%d-%m-%Y')
    new_date_string = date_object.strftime('%Y-%m-%d')
    obj['tanggal'] = new_date_string
    print(obj['kategori'])
    return render_template('editsuratmasuk.html', surat=obj, id=id)


@app.route("/list-surat-keluar")
def list_surat_keluar():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        list_surat = db.letters.find({'kategori':'SK'})
        jumlah_surat = db.letters.count_documents({'kategori':'SK'})
        return render_template('listsuratkeluar.html', list_surat=list_surat, jumlah_surat=jumlah_surat,user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    

@app.route("/add-surat-keluar")
def add_surat_keluar():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        return render_template('addsuratkeluar.html')
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    
@app.route("/add-surat-keluar-save", methods=['POST'])
def add_surat_keluar_save():
    nomor_surat_receiver = request.form.get('nomor_surat')
    kategori_receiver = request.form.get('kategori')
    pengirim_receiver = request.form.get('pengirim')
    tanggal_receiver = request.form.get('tanggal')
    tujuan_receiver = request.form['tujuan']
    perihal_receiver = request.form['perihal']
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')


    #simpan file di tmp/foo
    lampiran_receiver.save('/tmp/foo')
    #akses dan cek ukuran file pada tmp/foo dir
    file_size = os.stat('/tmp/foo').st_size
    extension_surat = lampiran_receiver.filename.split(".")[-1]
    #cek ukuan file
    if file_size <= 5*1000*1000:
        #cek extensi
        if extension_surat not in ALLOWED_FILE:
            flash('The file must be .docs, .doc, and .pdf ', 'error')
            return redirect(url_for('list_surat_keluar'))
        #simpan surat
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
        print(lampiran_receiver)
        filename = secure_filename(lampiran_receiver.filename) #secure file
        file_path = f"letters/{kategori_receiver}_{nomor_surat_receiver}_{datetime_to_tanggal}_{filename}" #membuat path baru
        lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
        surat["lampiran"] = file_path #menambah key value
        db.letters.insert_one(surat)
        flash('The letter has been successfully saved.', 'success')
        return redirect(url_for('list_surat_keluar'))
    else:
        flash('The file size exceeds 5 Mb.', 'error')
        return redirect(url_for('list_surat_keluar'))

@app.route("/surat-keluar/delete/<id>", methods=['GET'])
def surat_keluar_delete(id):
    db.letters.delete_one({'_id':ObjectId(id)})
    flash('The letter has been successfully deleted.','success')
    return redirect(url_for('list_surat_keluar'))


@app.route("/surat-keluar/update/<id>", methods=['GET','POST'])
def surat_keluar_update(id):
    obj = db.letters.find_one({'_id':ObjectId(id)})
    print(obj)
    if request.method == 'POST':
        print("Ngepost")
        tanggal_to_datetime = datetime.strptime(request.form['tanggal'], "%Y-%m-%d")
        datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
        lampiran_receiver =request.files['lampiran']
        lampiran_receiver.save('/tmp/foo')
        file_size = os.stat('/tmp/foo').st_size
        extension_surat = lampiran_receiver.filename.split(".")[-1]
        if file_size <= 5*1000*1000:
            #cek extensi
            if extension_surat not in ALLOWED_FILE:
                flash('The file must be .docs, .doc, and .pdf ', 'error')
                return redirect(url_for('list_surat_masuk'))
            filename = secure_filename(lampiran_receiver.filename) #secure file
            file_path = f"letters/{request.form['kategori']}_{request.form['nomor_surat']}_{datetime_to_tanggal}_{filename}" #membuat path baru
            print(file_path)
            lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
            data = {
                'nomor_surat':f"SK/{request.form['nomor_surat']}",
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
            return redirect(url_for('list_surat_keluar'))
    else:
        flash('The file size exceeds 5 Mb.', 'error')
        return redirect(url_for('list_surat_keluar'))
    obj['nomor_surat']=obj['nomor_surat'].replace("SK/",'')
    date_object = datetime.strptime(obj['tanggal'], '%d-%m-%Y')
    new_date_string = date_object.strftime('%Y-%m-%d')
    obj['tanggal'] = new_date_string
    print(obj['kategori'])
    return render_template('editsuratkeluar.html', surat=obj, id=id)




@app.route("/list-surat-pemberitahuan")
def list_surat_pemberitahuan():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        list_surat = db.letters.find({'kategori':'SP'})
        jumlah_surat = db.letters.count_documents({'kategori':'SP'})
        return render_template('listsuratpemberitahuan.html', list_surat=list_surat, jumlah_surat=jumlah_surat,user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    

@app.route("/add-surat-pemberitahuan")
def add_surat_pemberitahuan():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        return render_template('addsuratpemberitahuan.html')
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    
@app.route("/add-surat-pemberitahuan-save", methods=['POST'])
def add_surat_pemberitahuan_save():
    nomor_surat_receiver = request.form.get('nomor_surat')
    kategori_receiver = request.form.get('kategori')
    pengirim_receiver = request.form.get('pengirim')
    tanggal_receiver = request.form.get('tanggal')
    tujuan_receiver = request.form['tujuan']
    perihal_receiver = request.form['perihal']
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')


    #simpan file di tmp/foo
    lampiran_receiver.save('/tmp/foo')
    #akses dan cek ukuran file pada tmp/foo dir
    file_size = os.stat('/tmp/foo').st_size
    extension_surat = lampiran_receiver.filename.split(".")[-1]
    #cek ukuan file
    if file_size <= 5*1000*1000:
        #cek extensi
        if extension_surat not in ALLOWED_FILE:
            flash('The file must be .docs, .doc, and .pdf ', 'error')
            return redirect(url_for('list_surat_pemberitahuan'))
        #simpan surat
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
        print(lampiran_receiver)
        filename = secure_filename(lampiran_receiver.filename) #secure file
        file_path = f"letters/{kategori_receiver}_{nomor_surat_receiver}_{datetime_to_tanggal}_{filename}" #membuat path baru
        lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
        surat["lampiran"] = file_path #menambah key value
        db.letters.insert_one(surat)
        flash('The letter has been successfully saved.', 'success')
        return redirect(url_for('list_surat_pemberitahuan'))
    else:
        flash('The file size exceeds 5 Mb.', 'error')
        return redirect(url_for('list_surat_pemberitahuan'))

@app.route("/surat-pemberitahuan/delete/<id>", methods=['GET'])
def surat_pemberitahuan_delete(id):
    db.letters.delete_one({'_id':ObjectId(id)})
    flash('The letter has been successfully deleted.','success')
    return redirect(url_for('list_surat_pemberitahuan'))


@app.route("/surat-pemberitahuan/update/<id>", methods=['GET','POST'])
def surat_pemberitahuan_update(id):
    obj = db.letters.find_one({'_id':ObjectId(id)})
    print(obj)
    if request.method == 'POST':
        tanggal_to_datetime = datetime.strptime(request.form['tanggal'], "%Y-%m-%d")
        datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
        lampiran_receiver =request.files['lampiran']

        lampiran_receiver.save('/tmp/foo')
        file_size = os.stat('/tmp/foo').st_size
        extension_surat = lampiran_receiver.filename.split(".")[-1]

        if file_size <= 5*1000*1000:
            #cek extensi
            if extension_surat not in ALLOWED_FILE:
                flash('The file must be .docs, .doc, and .pdf ', 'error')
                return redirect(url_for('list_surat_pemberitahuan'))
            filename = secure_filename(lampiran_receiver.filename) #secure file
            file_path = f"letters/{request.form['kategori']}_{request.form['nomor_surat']}_{datetime_to_tanggal}_{filename}" #membuat path baru
            print(file_path)
            lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
            data = {
                'nomor_surat':f"SP/{request.form['nomor_surat']}",
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
            return redirect(url_for('list_surat_pemberitahuan'))
        else:
            flash('The file size exceeds 5 Mb.', 'error')
            return redirect(url_for('list_surat_pemberitahuan'))
    obj['nomor_surat']=obj['nomor_surat'].replace("SP/",'')
    date_object = datetime.strptime(obj['tanggal'], '%d-%m-%Y')
    new_date_string = date_object.strftime('%Y-%m-%d')
    obj['tanggal'] = new_date_string
    print(obj['kategori'])
    return render_template('editsuratpemberitahuan.html', surat=obj, id=id)


@app.route("/list-surat-pengumuman")
def list_surat_pengumuman():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        list_surat = db.letters.find({'kategori':'SN'})
        jumlah_surat = db.letters.count_documents({'kategori':'SN'})
        return render_template('listsuratpengumuman.html', list_surat=list_surat, jumlah_surat=jumlah_surat,user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    

@app.route("/add-surat-pengumuman")
def add_surat_pengumuman():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        return render_template('addsuratpengumuman.html')
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))
    
@app.route("/add-surat-pengumuman-save", methods=['POST'])
def add_surat_pengumuman_save():
    nomor_surat_receiver = request.form.get('nomor_surat')
    kategori_receiver = request.form.get('kategori')
    pengirim_receiver = request.form.get('pengirim')
    tanggal_receiver = request.form.get('tanggal')
    tujuan_receiver = request.form['tujuan']
    perihal_receiver = request.form['perihal']
    lampiran_receiver = request.files['lampiran']
    keterangan_receiver = request.form.get('keterangan')


    #simpan file di tmp/foo
    lampiran_receiver.save('/tmp/foo')
    #akses dan cek ukuran file pada tmp/foo dir
    file_size = os.stat('/tmp/foo').st_size
    extension_surat = lampiran_receiver.filename.split(".")[-1]
    #cek ukuan file
    if file_size <= 5*1000*1000:
        #cek extensi
        if extension_surat not in ALLOWED_FILE:
            flash('The file must be .docs, .doc, and .pdf ', 'error')
            return redirect(url_for('list_surat_pengumuman'))
        #simpan surat
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
        print(lampiran_receiver)
        filename = secure_filename(lampiran_receiver.filename) #secure file
        file_path = f"letters/{kategori_receiver}_{nomor_surat_receiver}_{datetime_to_tanggal}_{filename}" #membuat path baru
        lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
        surat["lampiran"] = file_path #menambah key value
        db.letters.insert_one(surat)
        flash('The letter has been successfully saved.', 'success')
        return redirect(url_for('list_surat_pengumuman'))
    else:
        flash('The file size exceeds 5 Mb.', 'error')
        return redirect(url_for('list_surat_pengumuman'))

@app.route("/surat-pengumuman/delete/<id>", methods=['GET'])
def surat_pengumuman_delete(id):
    db.letters.delete_one({'_id':ObjectId(id)})
    flash('The letter has been successfully deleted.','success')
    return redirect(url_for('list_surat_pengumuman'))


@app.route("/surat-pengumuman/update/<id>", methods=['GET','POST'])
def surat_pengumuman_update(id):
    obj = db.letters.find_one({'_id':ObjectId(id)})
    print(obj)
    if request.method == 'POST':
        print("Ngepost")
        tanggal_to_datetime = datetime.strptime(request.form['tanggal'], "%Y-%m-%d")
        datetime_to_tanggal = tanggal_to_datetime.strftime('%d-%m-%Y')
        lampiran_receiver =request.files['lampiran']

        lampiran_receiver.save('/tmp/foo')
        file_size = os.stat('/tmp/foo').st_size
        extension_surat = lampiran_receiver.filename.split(".")[-1]

        if file_size <= 5*1000*1000:
            #cek extensi
            if extension_surat not in ALLOWED_FILE:
                flash('The file must be .docs, .doc, and .pdf ', 'error')
                return redirect(url_for('list_surat_pengumuman'))
            filename = secure_filename(lampiran_receiver.filename) #secure file
            file_path = f"letters/{request.form['kategori']}_{request.form['nomor_surat']}_{datetime_to_tanggal}_{filename}" #membuat path baru
            print(file_path)
            lampiran_receiver.save(os.path.join(BASE_DIR+'/lexiarchiver/static/', file_path)) #menyimpan file
            data = {
                'nomor_surat':f"SN/{request.form['nomor_surat']}",
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
            return redirect(url_for('list_surat_pengumuman'))
        else:
            flash('The file size exceeds 5 Mb.', 'error')
            return redirect(url_for('list_surat_pengumuman'))
    obj['nomor_surat']=obj['nomor_surat'].replace("SN/",'')
    date_object = datetime.strptime(obj['tanggal'], '%d-%m-%Y')
    new_date_string = date_object.strftime('%Y-%m-%d')
    obj['tanggal'] = new_date_string
    print(obj['kategori'])
    return render_template('editsuratpengumuman.html', surat=obj, id=id)


@app.route("/profile")
def profile():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(
            token_receive, SECRET_KEY,algorithms=['HS256']
        )
        user_info=db.users.find_one({'username':payload.get('id')})
        return render_template('profil.html',user_info=user_info)
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('dashboard'))


@app.route("/edit-profile")
def edit_profile():
    pass

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)