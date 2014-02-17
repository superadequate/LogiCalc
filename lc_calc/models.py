from django.db import models
from mezzanine.core.models import Slugged, RichText


class Named(models.Model):
    name = models.CharField(max_length=64, unique=True,
                            help_text="The name of this object (must be unique).")

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class LoanType(Named):
    pass


class LoanCompany(Slugged, RichText):
    """
    A loan company offers a set of loans.
    """
    logo = models.ImageField(upload_to='loan_company_logos', null=True, blank=True,
                             help_text='The logo image for the company (need to set a size - keep it small)')

    class Meta:
        ordering = ['title']


class LoanAdditionLookupValueType(Named):
    """
    The type of the addition
    """
    pass


class LoanAdditionLookup(models.Model):
    """
    Data lookup value for loan calculation
    """
    loan_company = models.ForeignKey(LoanCompany)
    loan_type = models.ForeignKey(LoanType)
    value_type = models.ForeignKey(LoanAdditionLookupValueType)
    credit_score = models.IntegerField(help_text="The minimum credit score for which this value is applicable.")
    value_index = models.IntegerField(help_text="The Addition lookup value (sheet column value).")
    value = models.FloatField(help_text="The value to use in the calculation.")

    class Meta:
        ordering = ['loan_company__title',
                    'loan_type__name',
                    'value_type__name',
                    '-credit_score',
                    'value_index']

    def __str__(self):
        return "{} | {} | {} | {} | {} | {} |".format(self.loan_company,
                                            self.loan_type,
                                            self.value_type,
                                            self.value_index,
                                            self.credit_score,
                                            self.value)