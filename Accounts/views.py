from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout


def login(request):
    context = dict()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('polls:index')
        else:
            context['error_msg'] = 'Login failed'
            return render(request, 'Accounts/login.html', context)
    else:
        return render(request, 'Accounts/login.html', context)


def logout(request):
    context = dict()
    auth_logout(request)
    return render(request, 'Accounts/login.html', context)
