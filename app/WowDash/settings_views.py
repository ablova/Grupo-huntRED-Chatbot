from django.shortcuts import render


def company(request):
    context={
        "title": "Company",
        "subTitle": "Settings - Company",
    }
    return render(request,"settings/company.html", context)

def currencies(request):
    context={
        "title": "Currrencies",
        "subTitle": "Settings - Currencies",
    }
    return render(request,"settings/currencies.html", context)

def languages(request):
    context={
        "title": "Languages",
        "subTitle": "Settings - Languages",
    }
    return render(request,"settings/languages.html", context)

def notification(request):
    context={
        "title": "Notification",
        "subTitle": "Settings - Notification",
    }
    return render(request,"settings/notification.html", context)

def notificationAlert(request):
    context={
        "title": "Notification Alert",
        "subTitle": "Settings - Notification Alert",
    }
    return render(request,"settings/notificationAlert.html", context)

def paymentGetway(request):
    context={
        "title": "Payment Getway",
        "subTitle": "Settings - Payment Getway",
    }
    return render(request,"settings/paymentGetway.html", context)

def theme(request):
    context={
        "title": "Theme",
        "subTitle": "Settings - Theme",
    }
    return render(request,"settings/theme.html", context)
