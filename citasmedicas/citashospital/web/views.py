# citasmedicas/citashospital/web/views.py
from copy import error
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.db import connection
import requests
from django.db import connection


def home(request):
    return redirect('listar_usuarios')
