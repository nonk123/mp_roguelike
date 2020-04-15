from django.shortcuts import render

def index(request):
    return render(request, "mp_roguelike/index.html", {
        "name": request.GET.get("name", "")
    })
