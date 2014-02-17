from django.contrib import admin
from lc_calc.models import (LoanType,
                            LoanCompany,
                            LoanAdditionLookupValueType,
                            LoanAdditionLookup)

admin.site.register(LoanType)
admin.site.register(LoanCompany)
admin.site.register(LoanAdditionLookupValueType)
admin.site.register(LoanAdditionLookup)
