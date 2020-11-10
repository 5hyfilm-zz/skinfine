import os
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from tensorflow.keras.models import Sequential, load_model
import numpy as np
import argparse
import imutils
import time
import uuid
import base64

IMG_WIDTH, IMG_HEIGHT = 224, 224

# final_answer_array = np.asarray(mean_answer)

UPLOAD_FOLDER = 'upload_folder/'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'JPG', 'JPEG', 'png'])

app = Flask(__name__)

def get_as_base64(url):
    return base64.b64encode(requests.get(url).content)

def ensemble_predict(test_data):
    test_data = load_img(test_data, target_size=(IMG_WIDTH, IMG_HEIGHT))
    test_data = img_to_array(test_data)
    test_data = np.true_divide(test_data, 255)
    test_data = np.expand_dims(test_data, axis=0)

    model_1 = tf.keras.models.load_model('model/PJ61403_model_1.h5')
    model_2 = tf.keras.models.load_model('model/PJ61403_model_2.h5')
    model_3 = tf.keras.models.load_model('model/PJ61403_model_3.h5')
    ans_1 = model_1.predict(test_data)
    ans_2 = model_2.predict(test_data)
    ans_3 = model_3.predict(test_data)
    all_answer_list = []
    for i in range(len(ans_1)):
        answer_list = []
        for j in range(len(ans_1[i])):
            mean_ans = (ans_1[i][j] + ans_2[i][j] + ans_3[i][j])/3
            answer_list.append(mean_ans)
        all_answer_list.append(answer_list)
        result = all_answer_list[0]
    mean_answer = np.argmax(result)

    if mean_answer == 0:
        print('Label: Atopic Dermatitis')
    elif mean_answer == 1:   
        print('Label: Normal')
    elif mean_answer == 2:
        print('Label: Psoriasis')
    elif mean_answer == 3:
        print('Label: Seborrhoeic Keratosis')
        
    return mean_answer

def my_random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index_template():
    return render_template('home.html')

@app.route('/home')
def home_template():
    return render_template('home.html')

@app.route('/about')
def helpus_template():
    return render_template('about.html')

@app.route('/predictor')
def predict():
    return render_template('predictor.html', label='')

@app.route('/predictor', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        import time
        start_time = time.time()
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            result = ensemble_predict(file_path)
            if result == 0:
                label = 'Atopic Dermatitis'
                cure = 'Self-healing at home'
    
            elif result == 1:
                label =	'Normal'
                cure = 'Self-healing at home'

            elif result == 2:
                label = 'Psoriasis'
                cure = 'Consult the doctor'

            elif result == 3:
                label = 'Seborrhoeic Keratosis'
                cure = 'Consult the doctor'

            print(result)
            print(file_path)
            filename = my_random_string(6) + filename

            os.rename(file_path, os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("--- %s seconds ---" % str (time.time() - start_time))
            return render_template('predictor.html', label=label, cure=cure, imagesource='upload_folder/' + filename)

@app.route('/upload_folder/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

app.add_url_rule('/upload_folder/<filename>', 'uploaded_file', build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/upload_folder':  app.config['UPLOAD_FOLDER']
})

@app.route('/contact')
def contact_template():
    return render_template('contact.html')

if __name__ == "__main__":
    app.debug=False
    app.run(host='0.0.0.0', port=5000)
