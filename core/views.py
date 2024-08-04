from django.shortcuts import render, HttpResponse, redirect
from .models import *
from .forms import *
import face_recognition
import urllib3
import json
from urllib.parse import urlencode
import cv2
import traceback
import numpy as np
from django.db.models import Q
from playsound import playsound
import os
import dlib
from PIL import Image
import africastalking
from datetime import datetime

###################################################################################################
######################### SEND SMS FUNCTIONALITY ###########################
######################################################################## 
username = "sandbox"
api_key = "25692d2b27eff3cf722b6080bb0c0d6e5172eeca341af3948832663d13d951eb"

africastalking.initialize(username, api_key)
sms = africastalking.SMS

def sms_callback(message, profile):
    send_sms(message, profile, username, api_key)

def send_sms(message, profile, username, api_key, ):
    try:
        # Check if the student has already boarded and sent an SMS
        if profile.present:
            print("SMS already sent for this student.")
            return
        # Define the endpoint URL
        url = "https://api.sandbox.africastalking.com/version1/messaging"

        # Create an HTTP pool manager
        http = urllib3.PoolManager()

        # Define the headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "apiKey": api_key,
        }

        # Construct the payload data
        payload = {
            "username": username,
            "to": profile.parent_phone,
            "message": message,
            "from": "22824"
        }

        # Encode the payload data
        encoded_payload = urlencode(payload)
        response = http.request("POST", url, body=encoded_payload, headers=headers)

        # Check the response status
        if response.status == 201:
            data = json.loads(response.data.decode("utf-8"))
            print("SMS sent successfully:", data) 
            return data 
        else:
            print("Failed to send SMS:", response.data) 
            return {"status": "error", "description": response.data.decode("utf-8")} 
    except Exception as e:
        print(f"We have a problem: {e}")
        return {"status": "error", "description": str(e)}

###################################################################################################
###################### FACE RECOGNITION FUNCTION ######################
########################################################################
last_face = 'no_face'
current_path = os.path.dirname(__file__)
sound_folder = os.path.join(current_path, 'sound/')
face_list_file = os.path.join(current_path, 'face_list.txt')
sound = os.path.join(sound_folder, 'beep.wav')
# index function 
def index(request):
    scanned = LastFace.objects.all().order_by('date').reverse()
    present = Student.objects.filter(present=True).order_by('updated').reverse()
    absent = Student.objects.filter(present=False)
    students = Student.objects.all()
    context = {
        'scanned': scanned,
        'present': present,
        'absent': absent,
        'students': students,
    }
    return render(request, 'core/index.html', context)
# Ajax function
def ajax(request):
    last_face = LastFace.objects.last()
    context = {
        'last_face': last_face
    }
    return render(request, 'core/ajax.html', context)

##############################################################################################################

def scan(request):

    global last_face

    known_face_encodings = []
    known_face_names = []

    profiles = Student.objects.all()
    for profile in profiles:
        person = profile.image
        image_of_person = face_recognition.load_image_file(f'media/{person}')
        person_face_encoding = face_recognition.face_encodings(image_of_person)[0]
        known_face_encodings.append(person_face_encoding)
        known_face_names.append(f'{person}'[:-4])


    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Does not Match"

                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    profile = Profile.objects.get(Q(image__icontains=name))
                    if profile.present == True:
                        pass
                    else:
                        profile.present = True
                        profile.save()

                    if last_face != name:
                        last_face = LastFace(last_face=name)
                        last_face.save()
                        last_face = name
                        PlaySound(sound)
                    else:
                        pass

                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 0.5, (255, 255, 255), 1)

        cv2.imshow('Taking Attendence', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return HttpResponse('scaner closed', last_face)

################################################################################################
def profiles(request):
    profiles = Student.objects.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'core/profiles.html', context)
    
############################################################################################

def details(request):
    try:
        last_face = LastFace.objects.last()
        profile = Student.objects.get(Q(image__icontains=last_face))
    except:
        last_face = None
        profile = None

    context = {
        'profile': profile,
        'last_face': last_face
    }
    return render(request, 'core/details.html', context)


def add_profile(request):
    form = StudentForm
    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('profiles')
    context={'form':form}
    return render(request,'core/add_profile.html',context)


def edit_profile(request,id):
    profile = Student.objects.get(id=id)
    form = StudentForm(instance=profile)
    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES,instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profiles')
    context={'form':form}
    return render(request,'core/add_profile.html',context)


def delete_profile(request,id):
    profile = Student.objects.get(id=id)
    profile.delete()
    return redirect('profiles')


def clear_history(request):
    history = LastFace.objects.all()
    history.delete()
    return redirect('index')


def reset(request):
    profiles = Student.objects.all()
    for profile in profiles:
        if profile.present == True:
            profile.present = False
            profile.save()
        else:
            pass
    return redirect('index')
