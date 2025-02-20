from django.shortcuts import render

def addUser(request):
    context={
        "title": "Add User",
        "subTitle": "Add User",
    }
    return render(request, "users/addUser.html", context)

def usersGrid(request):
    context={
        "title": "Users Grid",
        "subTitle": "Users Grid",
    }
    return render(request, "users/usersGrid.html", context)

def usersList(request):
    context={
        "title": "Users List",
        "subTitle": "Users List",
    }
    return render(request, "users/usersList.html", context)

def viewProfile(request):
    context={
        "title": "View Profile",
        "subTitle": "View Profile",
    }
    return render(request, "users/viewProfile.html", context)
