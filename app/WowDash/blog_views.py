from django.shortcuts import render

def addBlog(request):
    context={
        "title": "Add Blog",
        "subTitle": "Add Blog",
    }
    return render(request, "blog/addBlog.html", context)

def blog(request):
    context={
        "title": "Blog",
        "subTitle": "Blog",
    }
    return render(request, "blog/blog.html", context)

def blogDetails(request):
    context={
        "title": "Blog Details",
        "subTitle": "Blog Details",
    }
    return render(request, "blog/blogDetails.html", context)
