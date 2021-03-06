from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from .models import Verse, User_verses

import simplejson as json
import requests
import re

# Create your views here.
def index(request):
    # check if user is logged in, render user's homepage
    if request.user.is_authenticated:
        try:
            # get verse information, add to simple list
            verse_ids = User_verses.objects.filter(user_id=request.user.id)
            verses = [row.verse_id.reference for row in verse_ids]

        except User_verses.DoesNotExist:
            verses = ["No verses Saved for this user"]

        # prepare user data, render template
        context = {
            "user": request.user,
            "firstPage": 1,
            "verses": verses,
        }
        return render(request, "mem_app/index.html", context)
    else:
        return redirect(reverse("login_view"))

def login_view(request):
    if request.method == "POST":
        # logout user just in case
        logout(request)

        # get user info
        username = request.POST["username"]
        password = request.POST["password"]

        # authenticate login
        user = authenticate(request, username=username, password=password)

        # log user in if valid
        if user is not None:
            login(request, user)
            return redirect(reverse("index"))

        # render login, w/ error message
        else:

            messages.error(request, "Invalid Credentials")
            return redirect(reverse("login_view"))

    return render(request, "mem_app/login.html")

def logout_view(request):
    # logout user, redirect to login page
    logout(request)
    return HttpResponseRedirect(reverse("login_view")) 
    
def register(request):
    if request.method == "POST":
        # get user info
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        # check for empty inputs
        if "" in {username, email, password}:
            messages.error(request, "All fields must be filled out")
            return HttpResponseRedirect(reverse("register"))

        # ensure password matches
        if password != request.POST["confirm_pw"]:
            messages.error(request, "Passwords do not match")
            return HttpResponseRedirect(reverse("register"))

        # check that email address is in a correct format
        # Not a full proof regex
        regex = re.compile(r".+@.+\.[A-Za-z]{2,4}$")
        if not regex.match(email):
            messages.error(request, "Invalid Email")
            return HttpResponseRedirect(reverse("register"))

        # attempt to create new user
        try:
            new_user = User.objects.create_user(username, email, password)
        except:
            messages.error(request, "Account creation failed")
            messages.error(request, "Try a different username")
            return HttpResponseRedirect(reverse("register"))

        # save new user info
        new_user.first_name = username
        new_user.save()

        # redirect to login
        messages.success(request, "Account Created")
        return HttpResponseRedirect(reverse('login_view'))

    # GET requests
    # logout user
    logout(request)
    return render(request, "mem_app/register.html")

def search(request, page_number):
    # check if user is logged in
    if not request.user.is_authenticated:
        return redirect(reverse("login_view"))

    # get user's verses
    try:
        # get verse information, add to simple list
        verse_ids = User_verses.objects.filter(user_id=request.user.id)
        verses = [row.verse_id.reference for row in verse_ids]
    except User_verses.DoesNotExist:
        verses = ["No verses found"]

    # check for empty search field
    user_query = request.GET["search_q"]

    if user_query == "":
        context = {
            "login": True,
            "user": request.user,
            "firstPage": 1,
            "message": "Error: Search field empty",
            "verses": verses
        }

        # render error message
        return render(request, "mem_app/index.html", context)
    
    if not user_query.isalpha():
        # first search for specific reference
        url = "https://api.esv.org/v3/passage/text/"
        headers = {"Authorization": "Token d81190f088982d48aea54a7154ff7b3e5b9a4dbe"}
        params = {
            "q": user_query,
            "include-verse-numbers": False,
            "include-first-verse-numbers": False,
            "include-passage-references": False,
            "include-footnotes": False,
            "include-footnote-body": False,
            "include-headings": False,
            "include-short-copyright": False,
        }

        res = requests.get(url, params=params, headers=headers)
        res_dict = res.json()


        # if valid reference
        if res_dict["canonical"]:

            # prepare response data
            passages = []
            for passage in res_dict["passages"]:
                passages.append({"reference": res_dict["canonical"], "content": passage})

            context = {
                "passages": passages,
                "user": request.user,
                "message": "",
                "firstPage": 1,
                "search_q": user_query,
                "verses": verses,
            }
            return render(request, "mem_app/index.html", context)
    
    # attach API token, prepare url
    headers = {"Authorization": "Token d81190f088982d48aea54a7154ff7b3e5b9a4dbe"}
    params = {
        "q": user_query,
        "page": page_number,
    }
    url = f"https://api.esv.org/v3/passage/search/"

    # send request, convert json response to a python dictionary
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
        "verses": verses,
    }
    return render(request, "mem_app/index.html", context)

def add_verse(request):
    if not request.user.is_authenticated:
        return redirect(revers("login_view"))

    if request.method == "POST":
        # get JSON string, convert to a dict
        data = json.loads(request.body)
        data["text"] = data["text"].lstrip()
        data["text"] = data["text"].rstrip("\n")

        # add verse to database, pass error if verse is already in database
        new_verse = Verse(reference=data["ref"], text=data["text"])

        try:
            new_verse.save()
        except:
            pass

        # attach verse to User (if relationship does not exist), save changes
        check_rel = User_verses.objects.filter(verse_id=Verse.objects.get(reference=data["ref"]), user_id=request.user.id)
        if len(check_rel) == 0:
            new_rel = User_verses(verse_id=Verse.objects.get(reference=data["ref"]), user_id=request.user.id)
            new_rel.save()

        return HttpResponse(json.dumps({"ref": data["ref"], "text": data["text"]}))

def memorize(request, reference):
    # check if user is logged in
    if not request.user.is_authenticated:
        return redirect(reverse("login_view"))

    try:
        # get verse information, add to simple list
        verse_ids = User_verses.objects.filter(user_id=request.user.id)
        verses = [row.verse_id.reference for row in verse_ids]
    except User_verses.DoesNotExist:
        verses = ["No verses saved for this user"]

    context = {
        "ref": reference,
        "verses": verses,
    }
    return render(request, "mem_app/memorize.html", context)

def verse(request, reference):
    # check if user is logged in
    if not request.user.is_authenticated:
        return redirect(reverse("login_view"))

    user_refs = []
    verse_data = {
        "ref": reference,
    }

    # get user's verses
    verses = User_verses.objects.filter(user_id=request.user.id)

    for verse in verses:
        user_refs.append(verse.verse_id.reference)

    # check if reference appear in user's verses, if so send data
    if reference in user_refs:
        verse_obj = Verse.objects.get(reference=reference)
        user_verse = User_verses.objects.get(user_id=request.user.id, verse_id=verse_obj)
        print(user_verse.score)
        verse_data["text"] = verse_obj.text
        verse_data["score"] = user_verse.score
    else:
        verse_data["text"] = None

    return HttpResponse(json.dumps(verse_data))

def update_score(request):
    # check if user is logged in
    if not request.user.is_authenticated:
        return redirect(reverse("login_view"))
        
    # get data from POST
    data = json.loads(request.body)

    # get user's verse
    verse = Verse.objects.get(reference=data["reference"])
    user_verse = User_verses.objects.get(user_id=request.user.id, verse_id=verse)

    # update score
    user_verse.score = data["score"]
    user_verse.save(update_fields=["score"])

    # return success
    return HttpResponse(json.dumps({"status": "success"}))
