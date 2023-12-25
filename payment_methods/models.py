from django.db import models

from school.models import School
from models import ParentModel


class PaymentMethod(ParentModel):
    name = models.CharField(max_length=255)
    is_cash = models.BooleanField(default=False, null=True)
    is_bank = models.BooleanField(default=False, null=True)
    school = models.ForeignKey(School, default=None, null=True, on_delete=models.CASCADE, related_name="paymentmethods")

    def __str__(self):
        return self.name
