from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from .models import Verse, User_verses
from json import dump
import requests

# Create your views here.
def index(request):
    # check if user is logged in
    if not request.user.is_authenticated:
        return render(request, "mem_app/login.html")

    # if yes, render user specific home page
    else:
        # TODO: get users's memory verse data
        context = {
            "user": request.user,
            "firstPage": 1,
        }
        return render(request, "mem_app/index.html", context)

def login_view(request):
    if request.method == "POST":
        # get user info
        username = request.POST["username"]
        password = request.POST["password"]

        # authenticate login
        user = authenticate(request, username=username, password=password)

        # log user in if valid
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))

        # render login, w/ error message
        else:
            return render(request, "mem_app/login.html", {"message": "Invalid Credentials"})

    return render(request, "mem_app/login.html")

def logout_view(request):
    # logout user, redirect to login page
    logout(request)
    return HttpResponseRedirect(reverse("login_view")) 
    
def register(request):
    if request.method == "POST":
        # get user info TODO: check for no input
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        # ensure confirm password
        if password != request.POST["confirm_pw"]:
            return render(request, "mem_app/register.html", {message: "Passwords do no Match"})

        # insert user info into the database, redirect to homepage
        new_user = User.objects.create_user(username, email, password)
        new_user.first_name = username
        new_user.save()
        return HttpResponseRedirect(reverse('index'))
    
    return render(request, "mem_app/register.html")

def search(request, page_number):
    # check for empty search field
    user_query = request.GET["search_q"]
    if user_query == "":
        context = {
            "user": request.user,
            "firstPage": 1,
            "message": "Error: Search field empty",
        }

        # render error message
        return render(request, "mem_app/index.html", context)
    
    # attach API token, prepare url
    headers = {"Authorization": "Token d81190f088982d48aea54a7154ff7b3e5b9a4dbe"}
    params = {
        "q": user_query,
        "page": page_number,
    }
    url = f"https://api.esv.org/v3/passage/search/"

    # send request, convert to json reponse to a python dictionary
    res = requests.get(url, params=params, headers=headers)
    res_dict = res.json()

    # prepare data, render search results
    nextPage = res_dict["page"] + 1
    previousPage = res_dict["page"] - 1
    message = ""
    if not res_dict["results"]:
        message = "No Search Results Found"
    context = {
        "passages": res_dict["results"],
        "user": request.user,
        "totalPages": res_dict["total_pages"],
        "firstPage": page_number,
        "currentPage": res_dict["page"],
        "search_q": user_query,
        "previousPage": previousPage,
        "nextPage": nextPage,
        "message": message,
    }
    return render(request, "mem_app/index.html", context)

def add_verse(request):
    if request.method == "POST":
        print(request.POST)
        return HttpResponse(dump({"result": True}))
    else:
        return HttpResponse(dump({"result": False}))