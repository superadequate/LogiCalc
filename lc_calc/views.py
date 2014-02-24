from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect

from lc_calc.models import LoanCompany, LoanCalculation
from lc_calc.forms import LoanCalculationForm


class LoanCompanyMixin(object):
    """
    Provides view with calculation and template with loan_company and calculation (if present)
    """
    def get_loan_company(self):
        # Add the loan company
        return get_object_or_404(
            LoanCompany,
            slug=self.kwargs['loan_company_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the loan company
        context['loan_company'] = self.get_loan_company()

        calculation = self.get_calculation()
        if calculation is not None:
            context['calculation'] = calculation

        return context

    def get_calculation(self):
        """
        If there is a calculation already available to this session, get it.
        """
        try:
            return self.calculation
        except AttributeError:
            calculation_id = self.request.session.get('calculation_id', None)
            if calculation_id is None:
                self.calculation = None
            else:
                self.calculation = LoanCalculation.objects.get(id=calculation_id)
            return self.calculation

    def put_calculation(self, calculation):
        """
        Record calculation in the session and on self
        """
        self.request.session['calculation_id'] = calculation.id
        self.request.session.set_expiry(3600)  # remember it for an hour


class CalculationView(LoanCompanyMixin, FormView):
    template_name = "lc_calc/calculation.html"
    form_class = LoanCalculationForm
    model = LoanCalculation

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        calculation = self.get_calculation()
        if calculation is not None:
            kwargs['instance'] = calculation
        return kwargs

    def form_valid(self, form):
        form.save()
        self.put_calculation(form.instance)
        return redirect("calculation", **self.kwargs)


class ContactView(LoanCompanyMixin, TemplateView):
    template_name = "lc_calc/contact.html"
    pass