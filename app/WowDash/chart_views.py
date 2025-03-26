from django.shortcuts import render

def columnChart(request):
    context={
        "title": "Column Chart",
        "subTitle": "Components / Column Chart",
    }
    return render(request, "chart/columnChart.html", context)
    
def lineChart(request):
    context={
        "title": "Line Chart",
        "subTitle": "Components / Line Chart",
    }
    return render(request, "chart/lineChart.html", context)
    
def pieChart(request):
    context={
        "title": "Pie Chart",
        "subTitle": "Components / Pie Chart",
    }
    return render(request, "chart/pieChart.html", context)
    