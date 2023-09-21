from flask import Flask, render_template, url_for, redirect, request, make_response,Response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField , EmailField, IntegerField 
from wtforms.validators import InputRequired, Length, ValidationError ,EqualTo
from flask_bcrypt import Bcrypt
import pandas as pd
import numpy as np
import math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph ,Spacer ,Image
from reportlab.lib.styles import getSampleStyleSheet , ParagraphStyle
from datetime import datetime
from io import BytesIO
import io






#Ngebaca df jadi gramediacsv.csv    ngubah ; jadi separator atau pemisah
df = pd.read_csv('gramediaCSV.csv', sep= ";" , encoding='latin-1')




app = Flask(__name__, template_folder='Template')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column (db.String(20), nullable=False)
    
    
    
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    email = EmailField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Email"})
    
    confirm_password = PasswordField(validators=[
                              InputRequired(), EqualTo('password', message='Passwords must match')], render_kw={"placeholder": "Confirm Password"})
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    

    submit = SubmitField('Login')


class SearchForm(FlaskForm):
    search_query = StringField(validators=[InputRequired()])
    submit = SubmitField('Search')

class LimitForm(FlaskForm):
    limit = IntegerField('Limit')
    submit = SubmitField('Tampilkan')



    
    @app.route('/', methods= ['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    if user.username == 'admin123':
                        return redirect(url_for('tambahbuku'))
                    return redirect(url_for('halaman'))
        return render_template('awal.html', form=form)
    
    
    
    
    @app.route('/hasilrekom', methods=['GET', 'POST'])
    def halaman():
        user_greeting = f"Hi, {current_user.username}"  # Generate the personalized greeting

        page = int(request.args.get('page', 1))  
        items_per_page = 15
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page

        if request.method == 'POST':
            judul_genre = request.form.get('judul_genre')
            limit = int(request.form['limit'])
            

          
            

            # Filter
            filtered_data = df[
                (df['judul'].str.contains(judul_genre, case=False)) |
                (df['genre'].str.contains(judul_genre, case=False))
            ]

            # Rendering
            sorting = filtered_data.sort_values(by='rating_count' , ascending=False)
            data_to_display = sorting[start_index:end_index].to_dict(orient='records')
            
                    # Store data in the session
            session['pdf_data'] = data_to_display 
            
            
            

            total_items = len(filtered_data)
            num_pages = (total_items + items_per_page - 1 )
            
        

            return render_template('hasilrekom.html',  data=data_to_display, limit=limit, current_page=page, num_pages=num_pages)
            

        return render_template('halaman.html', user_greeting=user_greeting, current_page=page)


    @app.route('/register', methods= ['GET', 'POST'])
    def register():
        form = RegisterForm()
        
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password , email=form.email.data) 
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

        return render_template('halamanreg.html', form=form)
    
    
    
    @app.route('/halaman', methods=['GET', 'POST'])
    def hasilrekom():
        user_greeting = f"Hi, {current_user.username}"
        page = int(request.args.get('page', 1))  # Get the current page from query parameters
        items_per_page = 9
        
        

        
        data = request.args.getlist('data')  # list dictionary string
      

     
        
        num_pages = math.ceil(items_per_page)

        # Rendering
        
      
   
        return render_template('halaman.html', user_greeting=user_greeting, data=data, current_page=page, num_pages=num_pages)
    
    
    @app.template_filter('sort_by_rating_count')
    def sort_by_rating_count(data):
        
      
        
        return sorted(by='rating_count', ascending=False)    
    
    @app.route('/increment_review/<int:book_id>', methods=['POST'])
    def increment_review(book_id):
        # Find the index of the row with the matching no_id
        index = df.index[df['no_id'] == book_id].tolist()[0]
        
        # Increment the review_count by 1 for the specified row
        df.at[index, 'rating_count'] += 1
        
        # Save the modified DataFrame to the CSV file
        df.to_csv('gramediaCSV.csv', sep=';', index=False)
        
        # Get the page parameter from the request or default to 1
        page = request.form.get('page', 1)
        
        return redirect(url_for('halaman', page=page))
    

    @app.route('/tambahbuku', methods=['GET', 'POST'])
    def tambahbuku():
        global df  # Declare df global

        if request.method == 'POST':
            judul = request.form['judul']
            author = request.form['author']
            genre = request.form['genre']
            penerbit = request.form['penerbit']

            # Read 
            df = pd.read_csv('gramediaCSV.csv', sep=';', encoding='latin-1')

            # Create 
            new_buku = {
                'judul': judul,
                'author': author,
                'penerbit': penerbit,
                'isBestSeller': 0,  # Default 
                'original_rating': 0,   
                'adjusted_rating': 0,   
                'rating_count': 0,  
                'review_count': 0,  
                'genre': genre,
                'no_id': max(df['no_id']) + 1  # unique key
            }

            # concat
            new_row = pd.DataFrame(new_buku, index=[0])
            df = pd.concat([df, new_row], ignore_index=True)

            # update save
            df.to_csv('gramediaCSV.csv', sep=';', index=False)

            return render_template('tambahbuku.html')

        # nge get
        return render_template('tambahbuku.html')




    @app.route('/edit_buku/<no_id>', methods=['GET', 'POST'])
    def edit_buku(no_id):
        global df  # Declare df as a global variable

        if request.method == 'GET':
            # ambil dari df
            book_to_edit = df[df['no_id'] == int(no_id)].iloc[0]
            return render_template('editbuku.html', book=book_to_edit)
        
        if request.method == 'POST':
            # Update 
            df.loc[df['no_id'] == int(no_id), ['judul', 'author', 'genre', 'penerbit']] = [
                request.form['judul'], request.form['author'], request.form['genre'], request.form['penerbit']
            ]
            
            # Update csv
            df.to_csv('gramediaCSV.csv', sep=';', index=False)
            
            # Reload the DataFrame from CSV
            df = pd.read_csv('gramediaCSV.csv', sep=';', encoding='latin-1')
            
            return redirect(url_for('listbuku', page=1))
     
        
        
    @app.route('/listbuku/<page>', methods=['GET', 'POST'])
    def listbuku(page):
        global df  # Declare df as a global variable

        if request.method == 'POST':
            book_id_to_delete = request.form.get('delete_book')
            if book_id_to_delete:
                
                df = df[df['no_id'] != int(book_id_to_delete)]
                df.to_csv('gramediaCSV.csv', sep=';', index=False)
                return redirect(url_for('listbuku', page=1))

        books_per_page = 3
        start_index = (int(page) - 1) * books_per_page
        end_index = start_index + books_per_page

        # untuk display buku ini dari awal sampe akhir muncul dari dataframe
        books_to_display = df[start_index:end_index].to_dict(orient='records')

        session ['pdf_data'] = books_to_display
        
        
        num_books = len(df)
        num_pages = (num_books + books_per_page - 1) // books_per_page  # menghitung halaman paginasi

        return render_template('daftarbuku.html', books=books_to_display, page=int(page), num_pages=num_pages)
    
    
    @app.route('/daftaruser/<int:page>', methods=['GET', 'POST'])
    def daftaruser(page):
        halaman_pengguna = 6
        mulai_index = (page - 1) * halaman_pengguna


        if request.method == 'POST':
            user_id_to_delete = request.form.get('delete_user')
            if user_id_to_delete:
                user_to_delete = User.query.get(user_id_to_delete)
                if user_to_delete:
                    db.session.delete(user_to_delete)
                    db.session.commit()

        users_tampil = User.query.offset(mulai_index).limit(halaman_pengguna).all()

        id_user = User.query.count()
        halaman_user = (id_user + halaman_pengguna - 1) // halaman_pengguna

        return render_template('daftaruser.html', users=users_tampil, page=page, halaman_user=halaman_user)

    @app.route('/cetakrekom')
    def cetakrekom():
        books_to_display = session.get('pdf_data',[])
        
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

      # Define styles for the date and time
        styles = getSampleStyleSheet()
        date_style = styles['Normal']
        time_style = styles['Normal']


                # Get current date and time
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime('%B %d, %Y')
        formatted_time = current_datetime.strftime('%I:%M %p')

                # Create Paragraphs for date and time
        date_paragraph = Paragraph(f"Date: {formatted_date}", date_style)
        time_paragraph = Paragraph(f"Time: {formatted_time}", time_style)
        
        logo = Image('../Buku Rekomendasi.ipynb dah jadi/static/gambar/logo.jpeg')
        
        table_data = [['No.', 'Judul', 'Penulis', 'Genre', 'Penerbit', 'rating Count']]

          
        for index, row in enumerate(books_to_display, start=1):
            table_data.append([
                index, row['judul'], row['author'], row['genre'], row['penerbit'], row['rating_count']
            ])
        
        
        table = Table(table_data, colWidths=[30, 280, 150, 100, 150, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.lightgoldenrodyellow),
            ('LINEABOVE', (0,0), (-1,0), 2, colors.green),
            ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 2, colors.green),
            ('ALIGN', (1,1), (-1,-1), 'LEFT')
        ]))

       
        doc.build([ Spacer(5,1,22),logo ,date_paragraph, Spacer(2,2) , time_paragraph , Spacer(1, 1), table])

        
        buffer.seek(0)

       
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=GramediaBuku.pdf'
        return response
    

    
    @app.route('/daftarrekom/<page>', methods=['GET', 'POST'])
    def daftarrekom(page):
        books_per_page = 8
        start_index = (int(page) - 1) * books_per_page
        end_index = start_index + books_per_page
        
        sorted_df = df.sort_values(by='rating_count', ascending=False)

        books_to_display = sorted_df[start_index:end_index].to_dict(orient='records')

        num_books = len(df) 
        num_pages = (num_books + books_per_page - 1) // books_per_page  # menghitung halaman paginasi

       
        session ['pdf_data'] = (books_to_display)

        return render_template('daftarrekom.html', books=books_to_display, page=int(page), num_pages=num_pages)


        



    @app.route('/generate_pdf')
    def generate_pdf():
        
        data_to_display = session.get('pdf_data', [])


       
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

       
        styles = getSampleStyleSheet()
        date_style = styles['Normal']
        time_style = styles['Normal']
        
        custom_style = ParagraphStyle(
            name='CustomStyle',
            fontName='Helvetica-Bold',  
            fontSize=22,  
            alignment=1,  #  (0=left, 1=center, 2=right)
            textColor=colors.blue, 
            # borderWidth=1, 
            # borderColor=colors.black,  
            # borderPadding=2, 
        )
        

        
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime('%B %d, %Y')
        formatted_time = current_datetime.strftime('%I:%M %p')

        
        tanggal = Paragraph(f"Jakarta, {formatted_date}", date_style)
        waktu = Paragraph(f"Waktu: {formatted_time}", time_style)
        


        logo = Image('../Buku Rekomendasi.ipynb dah jadi/static/gambar/logo.jpeg')
        
        table_data = [['No.', 'Judul', 'Penulis', 'Genre', 'Penerbit', 'rating Count']]

        # Populate the table_data using data_to_display
        for index, row in enumerate(data_to_display, start=1):
            table_data.append([
                index, row['judul'], row['author'], row['genre'], row['penerbit'], row['rating_count']
            ])

        
        table = Table(table_data, colWidths=[30, 280, 150, 100, 150, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.lightgrey),
            ('LINEABOVE', (0,0), (-1,0), 2, colors.green),
            ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 2, colors.green),
            ('ALIGN', (1,1), (-1,-1), 'LEFT')
        ]))

    

        
        text = "Hasil Rekomendasi"

        intro = Paragraph(text, custom_style)
                
                
        doc.build([
            Table([[logo, None]], colWidths=[777, None]),
            intro,
            Spacer(5, 1, 5),
            tanggal,
            waktu,
            
            Spacer(2, 2),
            table
        ])

       
        buffer.seek(0)

        
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=GramediaBuku.pdf'
        return response
    
    
    @app.route('/cetakuser')
    def cetakuser():
        # Fetch user data from the database
        users = User.query.all()

        # Create a PDF buffer and document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
      # Define styles for the date and time
      
        styles = getSampleStyleSheet()
        date_style = styles['Normal']
        time_style = styles['Normal']
      
                      # Get current date and time
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime('%B %d, %Y')
        formatted_time = current_datetime.strftime('%I:%M %p')
      
      
        date_paragraph = Paragraph(f"Date: {formatted_date}", date_style)
        time_paragraph = Paragraph(f"Time: {formatted_time}", time_style)
        
        logo = Image('../Buku Rekomendasi.ipynb dah jadi/static/gambar/logo.jpeg')
      
        styles = getSampleStyleSheet()
        date_style = styles['Normal']
        time_style = styles['Normal']


                # Get current date and time
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime('%B %d, %Y')
        formatted_time = current_datetime.strftime('%I:%M %p')



        # Define the table header
        table_data = [['No.', 'Username', 'Email']]

        # Populate the table_data using user data
        for index, user in enumerate(users, start=1):
            table_data.append([index, user.username, user.email])

        # Create the table and add it to the PDF document
        table = Table(table_data, colWidths=[30, 150, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.lightgoldenrodyellow),
            ('LINEABOVE', (0,0), (-1,0), 2, colors.green),
            ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 2, colors.green),
            ('ALIGN', (1,1), (-1,-1), 'LEFT')
        ]))
        
        # Build the document with paragraphs and table
        doc.build([ Spacer(5,1,22),logo ,date_paragraph, Spacer(2,2) , time_paragraph , Spacer(1, 1), table])

        # Seek back to the beginning of the buffer
        buffer.seek(0)

        # Create a response with the PDF content
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=GramediaBuku.pdf'
        return response
   
   
    @app.route('/cetakdafbuk')
    def cetakdafbuk():
        books_to_display = session.get('pdf_data',[])
        
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

      # Define styles for the date and time
        styles = getSampleStyleSheet()
        date_style = styles['Normal']
        time_style = styles['Normal']


                # Get current date and time
        current_datetime = datetime.now()
        formatted_date = current_datetime.strftime('%B %d, %Y')
        formatted_time = current_datetime.strftime('%I:%M %p')

                # Create Paragraphs for date and time
        date_paragraph = Paragraph(f"Date: {formatted_date}", date_style)
        time_paragraph = Paragraph(f"Time: {formatted_time}", time_style)
        
        logo = Image('../Buku Rekomendasi.ipynb dah jadi/static/gambar/logo.jpeg')
        # Define the data for the table header
        table_data = [['No.', 'Judul', 'Penulis', 'Genre', 'Penerbit', 'Review Count']]

          # Populate the table_data using data_to_display
        for index, row in enumerate(books_to_display, start=1):
            table_data.append([
                index, row['judul'], row['author'], row['genre'], row['penerbit'], row['review_count']
            ])
        
        # Create the table and add it to the PDF document
        table = Table(table_data, colWidths=[30, 280, 150, 100, 150, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),colors.lightgoldenrodyellow),
            ('LINEABOVE', (0,0), (-1,0), 2, colors.green),
            ('LINEABOVE', (0,1), (-1,-1), 0.25, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 2, colors.green),
            ('ALIGN', (1,1), (-1,-1), 'LEFT')
        ]))

        # Build the document with paragraphs and table
        doc.build([ Spacer(5,1,22),logo ,date_paragraph, Spacer(2,2) , time_paragraph , Spacer(1, 1), table])

        # Seek back to the beginning of the buffer
        buffer.seek(0)

        # Create a response with the PDF content
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=GramediaBuku.pdf'
        return response



    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    
    if __name__ == "__main__":
        with app.app_context():
            db.create_all()
        
        app.run(debug=True)
    


