from django.views.generic import TemplateView

from lc_calc.models import LoanCompany


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the loan company
        loan_companies = LoanCompany.objects.all()
        context['loan_companies'] = loan_companies
        return context
