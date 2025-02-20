from django.shortcuts import render

def assignRole(request):
    context={
        "title": "Role & Access",
        "subTitle": "Role & Access",
    }
    return render(request, "roles_and_access/assignRole.html", context)

def roleAccess(request):
    context={
        "title": "Role & Access",
        "subTitle": "Role & Access",
    }
    return render(request, "roles_and_access/roleAccess.html", context)

