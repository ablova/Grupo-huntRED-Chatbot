from django.shortcuts import render

def formValidation(request):
    context={
        "title": "Form Validation",
        "subTitle": "Form Validation",
    }
    return render(request,"forms/formValidation.html", context)

def formWizard(request):
    context={
        "title": "Wizard",
        "subTitle": "Wizard",
    }
    return render(request,"forms/formWizard.html", context)

def inputForms(request):
    context={
        "title": "Input Forms",
        "subTitle": "Input Forms",
    }
    return render(request,"forms/inputForms.html", context)

def inputLayout(request):
    context={
        "title": "Input Layout",
        "subTitle": "Input Layout",
    }
    return render(request,"forms/inputLayout.html", context)
