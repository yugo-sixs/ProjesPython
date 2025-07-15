from django.http import HttpResponse
from django.shortcuts import render
from .models import Article


def hola_Mundo(request):
    return HttpResponse("Hola Mundo")


def index(request):
    html = """
        <h1>inicio</h1>
        <p>Bienvenido Años hasta el 2050:</p>
        <ul>
   """
    year = 2021
    while year <= 2050:

        if year % 2 == 0:
            html += f"<li>{str(year)}</li>"

        year += 1

    html += "</ul>"
    html += "<p>Fin del listado</p>"
    return render(request, "index.html")


def articulos(request):
    articulos = Article.objects.all()
    articulos = Article.objects.filter(
        title__contains="Django"
    )
    return render(request, "articulos.html", {"articulos": articulos})
