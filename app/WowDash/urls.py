"""
URL configuration for WowDash project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from WowDash import ai_views
from WowDash import authentication_views
from WowDash import blog_views
from WowDash import chart_views
from WowDash import components_views
from WowDash import cryptoCurrency_views
from WowDash import dashboard_views
from WowDash import forms_views
from WowDash import home_views
from WowDash import invoice_views
from WowDash import roleAndAccess_views
from WowDash import settings_views
from WowDash import table_views
from WowDash import users_views

urlpatterns = [
    path('admin/', admin.site.urls),

# home routes

    path('', home_views.index),
    path('index', home_views.index, name='index'),
    path('blankpage', home_views.blankpage, name='blankpage'),
    path('calendar', home_views.calendar, name='calendar'),
    path('chat', home_views.chat, name='chat'),
    path('chat-profile', home_views.chatProfile, name='chatProfile'),
    path('comingsoon', home_views.comingsoon, name='comingsoon'),
    path('email', home_views.email, name='email'),
    path('faqs', home_views.faqs, name='faqs'),
    path('gallery', home_views.gallery, name='gallery'),
    path('kanban', home_views.kanban, name='kanban'),
    path('maintenance', home_views.maintenance, name='maintenance'),
    path('not-found', home_views.notFound, name='notFound'),
    path('pricing', home_views.pricing, name='pricing'),
    path('stared', home_views.stared, name='stared'),
    path('terms-conditions', home_views.termsAndConditions, name='termsAndConditions'),
    path('testimonials', home_views.testimonials, name='testimonials'),
    path('view-details', home_views.viewDetails, name='viewDetails'),
    path('widgets', home_views.widgets, name='widgets'),

# ai routes
    path('ai/code-generator', ai_views.codeGenerator, name='codeGenerator'),
    path('ai/code-generatorNew', ai_views.codeGeneratorNew, name='codeGeneratorNew'),
    path('ai/image-generator', ai_views.imageGenerator, name='imageGenerator'),
    path('ai/text-generator', ai_views.textGenerator, name='textGenerator'),
    path('ai/text-generator-new', ai_views.textGeneratorNew, name='textGeneratorNew'),
    path('ai/video-generator', ai_views.videoGenerator, name='videoGenerator'),
    path('ai/voice-generator', ai_views.voiceGenerator, name='voiceGenerator'),


# authentication routes
    path('authentication/forgot-password', authentication_views.forgotPassword, name='forgotPassword'),
    path('authentication/signin', authentication_views.signin, name='signin'),
    path('authentication/signup', authentication_views.signup, name='signup'),

# blog routes
    path('blog/add-blog', blog_views.addBlog, name='addBlog'),
    path('blog/blog', blog_views.blog, name='blog'),
    path('blog/blog-details', blog_views.blogDetails, name='blogDetails'),

# chart routes
    path('chart/column-chart', chart_views.columnChart, name='columnChart'),
    path('chart/line-chart', chart_views.lineChart, name='lineChart'),
    path('chart/pie-chart', chart_views.pieChart, name='pieChart'),

# components routes
    path('components/alerts', components_views.alerts, name='alerts'),
    path('components/avatars', components_views.avatars, name='avatars'),
    path('components/badges', components_views.badges, name='badges'),
    path('components/button', components_views.button, name='button'),
    path('components/calendar', components_views.calendar, name='calendarMain'),
    path('components/card', components_views.card, name='card'),
    path('components/carousel', components_views.carousel, name='carousel'),
    path('components/colors', components_views.colors, name='colors'),
    path('components/dropdown', components_views.dropdown, name='dropdown'),
    path('components/list', components_views.list, name='list'),
    path('components/pagination', components_views.pagination, name='pagination'),
    path('components/progressbar', components_views.progressbar, name='progressbar'),
    path('components/radio', components_views.radio, name='radio'),
    path('components/star-ratings', components_views.starRatings, name='starRatings'),
    path('components/switch', components_views.switch, name='switch'),
    path('components/tab-accordion', components_views.tabAndAccordion, name='tabAndAccordion'),
    path('components/tags', components_views.tags, name='tags'),
    path('components/tooltip', components_views.tooltip, name='tooltip'),
    path('components/typography', components_views.typography, name='typography'),
    path('components/upload', components_views.upload, name='upload'),
    path('components/videos', components_views.videos, name='videos'),

# cryptoCurrency routes

    path('crypto-currency/marketplace', cryptoCurrency_views.marketplace, name='marketplace'),
    path('crypto-currency/marketplace-details', cryptoCurrency_views.marketplaceDetails, name='marketplaceDetails'),
    path('crypto-currency/portfolio', cryptoCurrency_views.portfolio, name='portfolio'),
    path('crypto-currency/wallet', cryptoCurrency_views.wallet, name='wallet'),

# dashboard routes

    path('dashboard/index2', dashboard_views.index2, name="index2"),
    path('dashboard/index3', dashboard_views.index3, name="index3"),
    path('dashboard/index4', dashboard_views.index4, name="index4"),
    path('dashboard/index5', dashboard_views.index5, name="index5"),
    path('dashboard/index6', dashboard_views.index6, name="index6"),
    path('dashboard/index7', dashboard_views.index7, name="index7"),
    path('dashboard/index8', dashboard_views.index8, name="index8"),
    path('dashboard/index9', dashboard_views.index9, name="index9"),
    path('dashboard/index10', dashboard_views.index10, name="index10"),


# forms routes

    path('forms/form-validation', forms_views.formValidation, name="formValidation"),
    path('forms/form-wizard', forms_views.formWizard, name="formWizard"),
    path('forms/input-forms', forms_views.inputForms, name="inputForms"),
    path('forms/input-layout', forms_views.inputLayout, name="inputLayout"),

# invoices routes

    path('invoice/add-new', invoice_views.addNew, name='addNew'),
    path('invoice/edit', invoice_views.edit, name='edit'),
    path('invoice/list', invoice_views.list, name='invoiceList'),
    path('invoice/preview', invoice_views.preview, name='preview'),

# role and access routes

    path('role-access/assign-role', roleAndAccess_views.assignRole, name='assignRole'),
    path('role-access/role-access', roleAndAccess_views.roleAccess, name='roleAccess'),

#settings routes

    path('settings/company', settings_views.company, name='company'),
    path('settings/currencies', settings_views.currencies, name='currencies'),
    path('settings/languages', settings_views.languages, name='languages'),
    path('settings/notification', settings_views.notification, name='notification'),
    path('settings/notification-alert', settings_views.notificationAlert, name='notificationAlert'),
    path('settings/payment-getway', settings_views.paymentGetway, name='paymentGetway'),
    path('settings/theme', settings_views.theme, name='theme'),

# tables routes

    path('tables/basic-table', table_views.basicTable, name='basicTable'),
    path('tables/data-table', table_views.dataTable, name='dataTable'),

#users routes

    path('users/add-user', users_views.addUser, name='addUser'),
    path('users/users-grid', users_views.usersGrid, name='usersGrid'),
    path('users/users-list', users_views.usersList, name='usersList'),
    path('users/view-profile', users_views.viewProfile, name='viewProfile'),

]

