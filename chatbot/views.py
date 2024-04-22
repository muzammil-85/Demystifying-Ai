import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.models import User

from chatbot.video_generate.video_audio import generate_video
from .models import Chat
import requests

def generate_response(input_text):
    from openai import OpenAI

    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    completion = client.chat.completions.create(
  model="local-model", # this field is currently unused
  messages=[
    {"role": "user", "content": input_text}
  ],
  temperature=0.7,
)

    print(completion.choices[0].message.content)
    # API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b"
    # headers = {"Authorization": "Bearer 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"}

    # def query(payload):
    #     response = requests.post(API_URL, headers=headers, json=payload)
    #     return response.json()
        
    # output = query({
    #     "inputs": input_text,
    # })
    # response = output[0]['generated_text']
    try:
        responsetext =  completion.choices[0].message.content
    except:
        responsetext = 'Sorry, An error occur. Please try again.'
    return responsetext

def explain_shap(request):
    message = Chat.objects.last().message
    print('start generating video')
    
    generate_video(message)
    print('finish generating video')

    # Construct the video file path
    video_file_path = 'media/output_video.mp4'
    # Render the template and pass the video file path
    return render(request, 'generate_video.html', {'video_file': video_file_path})

def download_video(request):
    video_file_path = 'media/output_video.mp4'
    with open(video_file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="video/mp4")
        response['Content-Disposition'] = 'attachment; filename=output_video.mp4'
        return response

def chatbot(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        # Generate response using GPT-2
        responsetext = generate_response(message)

        # Print the generated response
        

        chat = Chat(user=request.user, message=message, response=responsetext, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': responsetext})
    return render(request, 'chatbot.html', {'chats': chats})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Password dont match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')