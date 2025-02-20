from django.shortcuts import render

def index2(request):
    context={
        "title": "Dashboard",
        "subTitle": "CRM",
    }
    return render(request, "dashboard/index2.html", context)

def index3(request):
    context={
        "title": "Dashboard",
        "subTitle": "eCommerce",
    }
    return render(request, "dashboard/index3.html", context)

def index4(request):
    context={
        "title": "Dashboard",
        "subTitle": "Cryptocracy",
    }
    return render(request, "dashboard/index4.html", context)

def index5(request):
    context={
        "title": "Dashboard",
        "subTitle": "Investment",
    }
    return render(request, "dashboard/index5.html", context)

def index6(request):
    context={
        "title": "Dashboard",
        "subTitle": "LMS / Learning System",
    }
    return render(request, "dashboard/index6.html", context)

def index7(request):
    context={
        "title": "Dashboard",
        "subTitle": "NFT & Gaming",
    }
    return render(request, "dashboard/index7.html", context)

def index8(request):
    context={
        "title": "Dashboard",
        "subTitle": "Medical",
    }
    return render(request, "dashboard/index8.html", context)

def index9(request):
    context={
        "title": "Analytics",
        "subTitle": "Analytics",
    }
    return render(request, "dashboard/index9.html", context)

def index10(request):
    context={
        "title": "POS & Inventory",
        "subTitle": "POS & Inventory",
    }
    return render(request, "dashboard/index10.html", context)
