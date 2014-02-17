from django.conf.urls import patterns, url

import lc_calc.views as views

urlpatterns = patterns(
    '',
    url("^co/(?P<loan_company_slug>.*)/$", views.CalculatorView.as_view(), name="calculator_view"))