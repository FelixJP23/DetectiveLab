from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm



def home(request):
    return render(request, 'Home.html')

def register_go_to(request):
    return render(request,'register.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request,user,backend='django.contrib.auth.backends.ModelBackend')
            return redirect('main_page') 
    
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


