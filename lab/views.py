from django.shortcuts import render

from .prototypes import discover


def index(request):
    return render(request, "lab/index.html", {"prototypes": discover()})
