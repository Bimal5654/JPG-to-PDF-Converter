from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.models import User
from .forms import UploadFileForm
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

def donate_view(request):
    return render(request, 'donate.html')

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']
        
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'User already exists')
                return redirect('signup')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email already exists')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, first_name=first_name, email=email, password=password1)
                user.save()
                messages.info(request, 'User created')
                return redirect('login')
        else:
            messages.info(request, 'Passwords do not match')
            return redirect('signup')
        return redirect('login')

    else:
        return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("dashboard")
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'login.html')

def upload_file(request):
    if request.method == 'POST':
        files = [request.FILES[f'file{i}'] for i in range(len(request.FILES))]

        valid_files = []

        for uploaded_file in files:
            if uploaded_file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                valid_files.append(uploaded_file)
            else:
                return HttpResponse("Please upload JPG, JPEG, or PNG files only.")
        
        pdf_output = io.BytesIO()
        pdf_canvas = canvas.Canvas(pdf_output, pagesize=A4)
        
        temp_files = []

        try:
            for i, uploaded_file in enumerate(valid_files):
                image = Image.open(uploaded_file)

                # Get rotation value
                rotation = int(request.POST.get(f'rotation{i}', 0))
                rotated_image = image.rotate(-rotation, expand=True)

                # Get dimensions of the rotated image
                img_width, img_height = rotated_image.size

                # Define the A4 page size in points (1 inch = 72 points)
                A4_WIDTH, A4_HEIGHT = A4
                    
               # Center the image on A4 page without scaling if it fits within the page size
                if img_width <= A4_WIDTH and img_height <= A4_HEIGHT:
                    new_width = img_width
                    new_height = img_height

                else:
                    # Calculate scaling factor to fit the image within A4 page
                    scale_factor = min(A4_WIDTH / img_width, A4_HEIGHT / img_height)
                    new_width = int(img_width * scale_factor)
                    new_height = int(img_height * scale_factor)

                
                # Calculate x, y positions to center image on A4
                x_position = (A4_WIDTH - new_width) / 2
                y_position = (A4_HEIGHT - new_height) / 2

                 # Resize the rotated image to fit within A4 page only if needed
                if img_width > A4_WIDTH or img_height > A4_HEIGHT:
                    rotated_image = rotated_image.resize((new_width, new_height), Image.BICUBIC)
                    
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file_path = temp_file.name
                temp_files.append(temp_file_path)
                rotated_image.save(temp_file_path, format='PNG')
                temp_file.close()

                # Draw the rotated image on the PDF canvas
                pdf_canvas.drawImage(temp_file_path, x_position, y_position, width=new_width, height=new_height)
                pdf_canvas.showPage()
                
            pdf_canvas.save()
            pdf_output.seek(0)

            filename, ext = os.path.splitext(valid_files[0].name)
            response = HttpResponse(pdf_output, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}.pdf"'.format(filename)
            return response

        finally:
            for temp_file_path in temp_files:
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
        
    return render(request, 'converter/upload.html')
