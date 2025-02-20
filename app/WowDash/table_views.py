from django.shortcuts import render

def basicTable(request):
    context={
        "title": "Basic Table",
        "subTitle": "Basic Table",
    }
    return render(request, "table/basicTable.html", context)

def dataTable(request):
    context={
        "title": "Data Table",
        "subTitle": "Data Table",
    }
    return render(request, "table/dataTable.html", context)
