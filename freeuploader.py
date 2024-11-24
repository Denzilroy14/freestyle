from flask import*
from datetime import date
import sqlite3
import os
from werkzeug.security import check_password_hash,generate_password_hash
app=Flask(__name__)
date=date.today()
app.config['UPLOADER']='uploades'
app.config['SECRET_KEY']='DenzilCreator'
DATABASE='userdb.db'
ADMINDATABASE='admin.db'
#-------------------Admin database-------------------------
def init_admindb():
    con=sqlite3.connect(ADMINDATABASE)
    con.row_factory=sqlite3.Row
    return con
def get_admindb():
    con=init_admindb()
    con.execute('CREATE TABLE IF NOT EXISTS admin(adminusername TEXT,adminpassword TEXT)')
    con.commit()
get_admindb()
#-------------------User database-------------------------
def init_db():
    con=sqlite3.connect(DATABASE)
    con.row_factory=sqlite3.Row
    return con
def get_db():
    if not os.path.exists(DATABASE):
        con=init_db()
        con.execute('CREATE TABLE IF NOT EXISTS userdb(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,name TEXT,email TEXT,password TEXT,filename TEXT,file_data BLOB,dateofreg TEXT)')
        con.commit()
        con=init_db()
get_db()
@app.route('/')
#--------------------------Home page url--------------------------------------
@app.route('/index')
def index():
    return render_template('homepage.html')
#------------------------------URL for sign in page-------------------------------------------------
@app.route('/signin',methods=['GET','POST'])
def signin():
    if request.method=='POST':
        name=request.form['name']#requesting user name
        email=request.form['email']#requesting user email
        username=request.form['username']#requesting user to create a username
        password=request.form['password']#requesting user to create a password
        confirm_password=request.form['confirm_password']#requesting user to confirm their password
        if not confirm_password:
            return redirect(url_for('signin'))#user gets redirected if confirm password do not match with user creted password
        final_password=generate_password_hash(password,method='pbkdf2:sha256')#hashing user created password for safety
        con=init_db()
        con.execute('INSERT INTO userdb(name,username,password,email,dateofreg)VALUES(?,?,?,?,?)',(name,username,final_password,email,date))
        con.commit()
        return redirect(url_for('login'))
    else:
        return render_template('signinpage.html')
#---------------------------------URL for login--------------------------------------------------
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        user_name=request.form['username']#requesting user to enetr username
        password=request.form['password']#requesting user to enter their password
        if user_name and password:
            con=init_db()
            user=con.execute('SELECT * FROM userdb WHERE username=?',(user_name,)).fetchone()
            if user and check_password_hash(user['password'],password):#unhashing user password safely
                session['user_id']=user['id']
                session['username']=user['username']
                return redirect(url_for('profile'))
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template('loginpage.html')
#--------------URL for users profile page to allow the to upload or download content-----------------------------------------------
@app.route('/profile')
def profile():
    return render_template('profile.html')
#----------------------------URL for user to upload their content---------------------------------------------------------------
@app.route('/upload',methods=['GET','POST'])
def upload():
    if request.method=='POST':
        file=request.files['file']
        if file:
            filename=file.filename
            filepath=os.path.join(app.config['UPLOADER'],filename)
            file.save(filepath)
            with open(filepath,'rb')as f:
                file_data=f.read()
                con=init_db()
                con.execute('INSERT INTO userdb(filename,file_data)VALUES(?,?)',(filename,file_data))
                con.commit()
                return redirect(url_for('profile'))
    else:
        return render_template('upload.html')
@app.route('/view')
def view():
    con=init_db()
    data=con.execute('SELECT * FROM userdb').fetchall()
    return render_template('downloadpage.html',data=data)
#------------------------------URL for user to download the content--------------------------------------------------------------
@app.route('/download/<int:id>')
def download(id):
    con=init_db()
    file=con.execute('SELECT filename,file_data FROM userdb WHERE id=?',(id,)).fetchall()
    if file:
        filename,file_data=file
        return file_data,200,{
            'Content-Disposition':f'attachment;filename={filename}'
            }
    else:
        return "<html><body><h1>File Not found</h1></body></html>"
#------------------------------Admin---------------------------------------#
password="DenzilRoy"
username="Roy123@bsc"
final_adminpassword=generate_password_hash(password,method='pbkdf2:sha256')
conn=init_admindb()
conn.execute('INSERT INTO admin(adminusername,adminpassword)VALUES(?,?)',(username,final_adminpassword))
conn.commit()
@app.route('/loginadmin',methods=['GET','POST'])
def loginadmin():
    if request.method=='POST':
        adminusername=request.form['adminusername']
        adminpassword=request.form['adminpassword']
        if adminusername and adminpassword:
            con=init_admindb()
            admin=con.execute('SELECT * FROM admin WHERE adminusername=?',(adminusername,)).fetchone()
            if admin and check_password_hash(admin['adminpassword'],adminpassword):
                return redirect(url_for('adminview'))
            else:
                return redirect(url_for('loginadmin'))
    else:
        return render_template('adminlogin.html')
#-----------------------------Url for admin to view user details--------------------------------------------------------
@app.route('/adminview')
def adminview():
    conn=init_db()
    data=conn.execute('SELECT name,username,email,filename,dateofreg,password FROM userdb').fetchall()
    return render_template('adminview.html',data=data)
@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        email=request.form['email']
        new_password=request.form['new_password']
        confirm_password=generate_password_hash(new_password,method='pbkdf2:sha256')
        if email and new_password:
            if 'user_id' in session:
                id=session['user_id']
                con=init_db()
                con.execute('UPDATE userdb SET password=? WHERE id=?',(confirm_password,id))
                con.commit()
                return redirect(url_for('login'))
            else:
                 return "<html><body><h1>Sorry! an error occured</h1></body></html>"
        else:
            return "<html><body><h1>Sorry! an error occured</h1></body></html>"
    else:
        return render_template('reset.html')
if __name__=='__main__':
    if not os.path.exists(app.config['UPLOADER']):
        os.mkdir(app.config['UPLOADER'])
    app.run(debug=True)