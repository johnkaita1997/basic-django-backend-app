# Create your views here.

import uuid

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice
from payment_in_kinds.models import PaymentInKind
from payment_in_kinds.serializers import PaymentInKindSerializer
from utils import SchoolIdMixin, IsAdminOrSuperUser, generate_unique_code, defaultCurrency, currentAcademicYear, \
    currentTerm
from voteheads.models import VoteHead
from .models import PIKReceipt
from .serializers import PIKReceiptSerializer


class PIKReceiptCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            with transaction.atomic():
                receipt_no = generate_unique_code("RT")
                default_Currency = defaultCurrency()
                year = currentAcademicYear()
                term = currentTerm()
                if not default_Currency:
                    Response({'detail': "Default Currency Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
                if not year:
                    Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
                if not term:
                    Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

                totalAmount = 0.00
                pik_values = request.data.get('pik_values', [])
                if pik_values:
                    totalAmount = sum(item['unit_cost'] * item['quantity'] for item in pik_values)

                pikreceipt_serializer = self.get_serializer(data=request.data)
                pikreceipt_serializer.is_valid(raise_exception=True)
                pikreceipt_serializer.validated_data['school_id'] = school_id
                pikreceipt_serializer.validated_data['receipt_No'] = receipt_no
                pikreceipt_serializer.validated_data['currency'] = default_Currency
                pikreceipt_serializer.validated_data['term'] = term
                pikreceipt_serializer.validated_data['year'] = year
                pikreceipt_serializer.validated_data['totalAmount'] = totalAmount
                pikreceipt_serializer.validated_data.pop('pik_values', [])
                pikreceipt_instance = pikreceipt_serializer.save()


                sum_Invoice_Amount = 0
                for value in pik_values:
                    value['receipt'] = pikreceipt_instance.id
                    value['school_id'] = school_id
                    value['student'] = pikreceipt_instance.student.id
                    value['votehead'] = pikreceipt_instance.votehead.id
                    value['amount'] = value['quantity'] * value['unit_cost']
                    paymentInKind_serializer = PaymentInKindSerializer(data=value)
                    paymentInKind_serializer.is_valid(raise_exception=True)
                    created_Pik = paymentInKind_serializer.save()

                    term_instance = created_Pik.receipt.term
                    year_instance = created_Pik.receipt.year
                    student = created_Pik.receipt.student

                    try:
                        invoice_instance = Invoice.objects.get(votehead=pikreceipt_instance.votehead, term=term_instance,year=year_instance, school_id=school_id, student=student)

                        if (invoice_instance.paid + created_Pik.amount) > invoice_instance.amount:
                            raise ValueError("Transaction 1 cancelled: Total paid amount exceeds total invoice amount")
                        else:
                            invoice_instance.paid += created_Pik.amount
                            invoice_instance.due = invoice_instance.amount - invoice_instance.paid
                            invoice_instance.save()

                            sum_Invoice_Amount += invoice_instance.amount

                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                if pikreceipt_instance.totalAmount > sum_Invoice_Amount:

                    overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True).first()
                    if not overpayment_votehead:
                        raise ValueError("No VoteHead found with is_Overpayment_Default set to true")

                    overpayment_Amount = sum_Invoice_Amount - pikreceipt_instance.totalAmount
                    newPIK = PaymentInKind(
                        student=pikreceipt_instance.student,
                        receipt=pikreceipt_instance,
                        amount=overpayment_Amount,
                        votehead=overpayment_votehead,
                        school_id=pikreceipt_instance.school_id
                    )
                    newPIK.save()

                    try:
                        invoice_instance = Invoice.objects.get(votehead=overpayment_votehead, term=term_instance,year=year_instance, school_id=school_id, student=student)
                        invoice_instance.paid += overpayment_Amount.amount
                        invoice_instance.save()
                        sum_Invoice_Amount += invoice_instance.amount

                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Records created successfully'}, status=status.HTTP_201_CREATED)



class PIKReceiptListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return PIKReceipt.objects.none()
        queryset = PIKReceipt.objects.filter(school_id=school_id)

        is_posted = self.request.query_params.get('posted', None)
        if is_posted is not None:
            queryset = queryset.filter(is_posted=True)
            print("It is reversed")
        else:
            queryset = queryset.filter(is_posted=False)
            print("It is not reversed")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)




class PIKReceiptDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = PIKReceipt.objects.all()
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = uuid.UUID(primarykey)
            return PIKReceipt.objects.get(id=id)
        except (ValueError, PIKReceipt.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not instance.is_posted:
            return Response({'detail': "You cannot update this record"},status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_update(serializer)
            return Response({'detail': 'PIKReceipt updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = instance.school_id
        term = instance.term
        year = instance.year

        if not instance.is_posted:
            return Response({'detail': "Item is already unposted"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                piks = PaymentInKind.objects.filter(receipt=instance).all()
                for pik_item in piks:
                    paid_Amount = pik_item.amount
                    votehead = pik_item.votehead
                    invoicelist = Invoice.objects.filter(school_id=school_id, term=term, year=year,votehead=votehead).all()
                    for invoice in invoicelist:
                        invoice.paid -= paid_Amount
                        invoice.due += paid_Amount
                        invoice.save()

                instance.is_posted = False
                instance.unposted_date = timezone.now()
                instance.save()

            return Response({'detail': "PIKReceipt Reversed Successfully"}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
