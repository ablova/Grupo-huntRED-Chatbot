from django.shortcuts import render

def codeGenerator(request):
    context={
        "title": "Code Generator",
        "subTitle": "Code Generator",
    }
    return render(request,"ai/codeGenerator.html", context)

def codeGeneratorNew(request):
    context={
        "title": "Code  Generator",
        "subTitle": "Code  Generator",
    }
    return render(request, "ai/codeGeneratorNew.html", context)

def imageGenerator(request):
    context={
        "title": "Image  Generator",
        "subTitle": "Image  Generator",
    }
    return render(request, "ai/imageGenerator.html", context)

def textGenerator(request):
    context={
        "title": "Text Generator",
        "subTitle": "Text Generator",
    }
    return render(request, "ai/textGenerator.html", context)

def textGeneratorNew(request):
    context={
        "title": "Text Generator",
        "subTitle": "Text Generator",
    }
    return render(request, "ai/textGeneratorNew.html", context)

def videoGenerator(request):
    context={
        "title": "Video Generator",
        "subTitle": "Video Generator",
    }
    return render(request, "ai/videoGenerator.html", context)

def voiceGenerator(request):
    context={
        "title": "Voice Generator",
        "subTitle": "Voice Generator",
    }
    return render(request, "ai/voiceGenerator.html", context)
