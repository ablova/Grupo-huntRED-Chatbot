from django.shortcuts import render

def forgotPassword(request):
    return render(request, "authentication/forgotPassword.html")

def signin(request):
    return render(request, "authentication/signin.html")

def signup(request):
    return render(request, "authentication/signup.html")
