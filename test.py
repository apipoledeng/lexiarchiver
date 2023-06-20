import os

# def get_file_size(file_path):
#     # Check if the file exists
#     if os.path.exists(file_path):
#         # Get the file size in bytes
#         file_size = os.path.getsize(file_path)
#         return file_size
#     else:
#         return None

# # Example usage
# file_path = '/home/mint/Downloads/videoplayback_4.docx'
# size_in_bytes = get_file_size(file_path)

# print(size_in_bytes<5242880)

# if size_in_bytes is not None:
#     print(f"File size: {size_in_bytes} bytes")
# else:
#     print("File not found or inaccessible.")


# import platform

# # Get the operating system type
# os_type = platform.system()

# # Print the operating system type
# print("Operating System:", os_type)

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print(BASE_DIR+'/lexiarchiver/static/ngetes/')


from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from flask import Flask,render_template,jsonify,request,redirect,url_for
from werkzeug.utils import secure_filename
client = MongoClient("mongodb+srv://kentang:eUenw9z4QIlEoGzW@cluster0.mjce1r3.mongodb.net/?retryWrites=true&w=majority")
db = client.lexiarchiver

book1 = {
    "title": "Harry Potter",
    "author": "J.K. Rowling",
    "rating": 90
}

x='admin123'
password_hash = hashlib.sha256(x.encode('utf-8')).hexdigest()

admin = {
    'username':'admin',
    'password':password_hash,
    'first_name':'Admin',
    'last_name':'TU',
    'phone':'080000000',
    'city':'Malang',
    'bio':'Administrator'

}
# Memasukan tiga documen book ke dalam koleksi books
# db.users.insert_one(admin)
kategori1 = {
    'kategori':"Surat Masuk",
    'code':'SM'
}
kategori2 = {
    'kategori':"Surat Keluar",
    'code':'SK'
}
kategori3 = {
    'kategori':"Surat Pemberitahuan",
    'code':'SP'
}
kategori4 = {
    'kategori':"Surat Pengumuman",
    'code':'SN'
}
# categories=[kategori1,kategori2, kategori3, kategori4]
# db.categories.insert_many(categories)

leeters = []

for i in range(1,10):
    surat = {
        'nomor_surat':f'0{i}',
        'kategori': 'SN',
        'tanggal':f'2023-03-{i}',
        'tujuan': f'Kepala Sekolah {i}',
        'perihal': 'Nganu',
        'pengirim':f'OSIS {i}',
        'keterangan':'',
        'lampiran':'letters/Njajal2-2023-03-11.docx',
        }
    leeters.append(surat)
db.letters.insert_many(leeters)

# sm = db.categories.find_one({'code':'SM'})
# print(sm)



# Update Aurthor dari buku berjudul "The Fisherman and the Fish" menjadi "Jimmy Kim"
# db.books.update_one({'title':'The Fisherman and the Fish'},{'$set':{'author':'Jimmy Kim'}})

# Delete buku dengan rating sama dengan 90
# db.books.delete_one({'rating':90})