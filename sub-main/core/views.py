from django.views.decorators.clickjacking import xframe_options_exempt
import numpy as np
import json 
import cv2
from django.shortcuts import render,HttpResponse,redirect
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators import gzip
from django.views.decorators.cache import cache_control
from .models import DocModel
from .forms import DocumentForm
from django.conf import settings
import tensorflow as tf
model = settings.MODEL

def index(request):
    return render(request, 'index.html', {})

def about(request):
    return render(request, 'about.html', {})

#main logic
class VideoCamera(object):
    def __init__(self, url=None):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.status = True
        self.org = (50, 80)
        self.fontScale = 1.4
        self.thickness = 3
        self.SIZE = (200,200)
        self.THRESH = 0.65
        self.url = 0 if url is None else "."+url
        self.video = cv2.VideoCapture(self.url)
        self.skipCount = 20
        self.prev = None
        self.fcount = 0

    className = ['Criminal', 'Normal']

    def __del__(self):
        self.video.release()

    def get_frame(self):
        ret, image = self.video.read()
        if not ret:
            self.status = False
            pass

        if self.fcount % self.skipCount == 0:
            tmp = cv2.resize(image, self.SIZE)
            tmp = tmp / 255.0
            pred = model.predict(np.array([tmp]))
            
            string = "Suspicious" if pred[0][0] > self.THRESH else "Peaceful"
            # string = "Suspicious" if pred[0][0] > pred[0][1] else "Peaceful" 
            string += f" {str(pred[0][0])}"
            self.prev = string

        else:
            string = self.prev

        color = (255, 255, 255)
        image = cv2.rectangle(image, (20, 20), (600, 100), (0, 200, 100), cv2.FILLED) if string.split(' ')[0] == 'Peaceful' else cv2.rectangle(
            image, (20, 20), (600, 100), (0, 0, 255), cv2.FILLED)
        image = cv2.putText(image, string, self.org, self.font,
                            self.fontScale, color, self.thickness, cv2.LINE_AA)
        ret, jpeg = cv2.imencode('.jpg', image)
        self.fcount += 1
        return jpeg.tobytes()

def gen(camera):
    while camera.status:
        frame = camera.get_frame()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

#####################################################################################
#for file upload
def dashboard(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('streamroom')
    else:
        form = DocumentForm()
        return render(request, 'dashboard.html', {'form': form})


#for live camera
def live(request):
    if request.method == 'POST':
        return redirect('livestreamroom')
    else: 
        return render(request, 'live.html')

##########################################################################################
#for file upload stream
@gzip.gzip_page
def Stream(request):
    try:
        entry = DocModel.objects.all().last()
        return StreamingHttpResponse(gen(VideoCamera(entry.vid.url)), content_type="multipart/x-mixed-replace;boundary=frame")
    except Exception as e:
        print("aborted")

#for stream.html page
@xframe_options_exempt
def StreamView(request):
    entry = DocModel.objects.all().last()
    if entry is None:
        messages.error(request, "No Video Files Yet!")
    return render(request, 'stream.html')


################################################################################################################
#for live stream
def LiveStream(request):
        camera = VideoCamera()
        return StreamingHttpResponse(gen(camera), content_type="multipart/x-mixed-replace;boundary=frame")

#for livestream.html page
@xframe_options_exempt
def LiveStreamView(request):
    entry = DocModel.objects.all().last()
    if entry is None:
        messages.error(request, "No Video Files Yet!")
    return render(request, 'livestream.html')