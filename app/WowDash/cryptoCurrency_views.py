from django.shortcuts import render

def marketplace(request):
    context={
        "title": "Market Place",
        "subTitle": "Market Place",
    }
    return render(request,"crypto_currency/marketplace.html", context)

def marketplaceDetails(request):
    context={
        "title": "Market Place Details",
        "subTitle": "Market Place Details",
    }
    return render(request,"crypto_currency/marketplaceDetails.html", context)

def portfolio(request):
    context={
        "title": "Portfolio",
        "subTitle": "Portfolio",
    }
    return render(request,"crypto_currency/portfolio.html", context)

def wallet(request):
    context={
        "title": "Wallet",
        "subTitle": "Wallet",
    }
    return render(request,"crypto_currency/wallet.html", context)
