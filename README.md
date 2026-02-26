<h3>

Project First time Setup :

use python 3.10

#create virtual environment
cd main
python -m venv venv
venv\Scripts\activate


pip install cmake
pip install https://github.com/Murtaza-Saeed/dlib/raw/master/dlib-19.22.99-cp310-cp310-win_amd64.whl
pip install face_recognition
pip install opencv-python
pip install django


# inside your venv
pip uninstall numpy
pip install numpy==1.26.4


pip install -r final.txt

#make model as this
python manage.py makemigrations core
python manage.py migrate core

</h3>

<h4>
it need to come like this:
Operations to perform:
  Apply all migrations: core
Running migrations:
  No migrations to apply.
</h4>



To Run normally:

venv\Scripts\activate
python manage.py runserver

http://127.0.0.1:8000/ (open this in browser)




cd sub-main
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt


To Run normally:

venv\Scripts\activate
python manage.py runserver




Overall run

python mainfile.py
