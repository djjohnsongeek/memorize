from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login_view"),
    path("logout", views.logout_view, name="logout_view"),
    path("register", views.register, name="register"),
    path("search/<int:page_number>", views.search, name="search"),
    path("add-verse", views.add_verse, name="add_verse"),
    path("memorize/<str:reference>", views.memorize, name="memorize"),
    path("verse/<str:reference>", views.verse, name="verse"),
    path("update-score", views.update_score, name="update_score"),
]