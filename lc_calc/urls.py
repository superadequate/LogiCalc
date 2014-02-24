from django.conf.urls import patterns, url

import lc_calc.views as views

urlpatterns = patterns(
    '',
    url("^co/(?P<loan_company_slug>.*)/calculation/$", views.CalculationView.as_view(), name="calculation"),
    url("^co/(?P<loan_company_slug>.*)/contact/$", views.ContactView.as_view(), name="contact"))