from django.contrib import admin
from lc_calc.utils.related_field_admin import RelatedFieldAdmin

from lc_calc.models import (LoanType,
                            LoanCompany,
                            LoanAdditionLookupValueType,
                            LoanAdditionLookup)

admin.site.register(LoanType)
admin.site.register(LoanCompany)
admin.site.register(LoanAdditionLookupValueType)


class LoanAdditionLookupAdmin(RelatedFieldAdmin):
    list_display = ['id',
                    'loan_company__title',
                    'loan_type__name',
                    'value_type__name',
                    'credit_score',
                    'value_index',
                    'value']
    list_filter = ['loan_company',
                   'loan_type',
                   'value_type',
                   'credit_score',
                   'value_index']
    search_fields = ['loan_company__title',
                     'loan_type__name',
                     'value_type__name']
    list_editable = ['credit_score', 'value_index', 'value']


admin.site.register(LoanAdditionLookup, LoanAdditionLookupAdmin)