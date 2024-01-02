# Create your views here.
from datetime import date, datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic_year.models import AcademicYear
from account_types.models import AccountType
from appcollections.models import Collection
from bank_accounts.models import BankAccount
from financial_years.models import FinancialYear
from invoices.models import Invoice
from items.models import Item
from payment_in_kind_Receipt.models import PIKReceipt
from payment_in_kinds.models import PaymentInKind
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from receipts.serializers import ReceiptSerializer
from reportss.models import ReportStudentBalance, StudentTransactionsPrintView, IncomeSummary, ReceivedCheque, \
    BalanceTracker, OpeningClosingBalances
from reportss.serializers import ReportStudentBalanceSerializer, StudentTransactionsPrintViewSerializer, \
    IncomeSummarySerializer, ReceivedChequeSerializer
from reportss.utils import getBalance, getBalancesByAccount
from students.models import Student
from students.serializers import StudentSerializer
from term.models import Term
from utils import SchoolIdMixin, currentAcademicYear, currentTerm, IsAdminOrSuperUser, check_if_object_exists
from voteheads.models import VoteHead
from voucher_items.models import VoucherItem
from vouchers.models import Voucher


class ReportStudentBalanceView(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def calculate(self, queryset, startdate, enddate, boardingstatus, term, year):

        print(f"1")
        if boardingstatus:
            queryset.filter(boarding_status=boardingstatus)

        reportsStudentBalanceList = []

        current_academic_year = currentAcademicYear()
        current_term = currentTerm()

        try:
            if year:
                year = get_object_or_404(AcademicYear, id=year)
            else:
                year = current_academic_year
        except:
            return []

        try:
            if term:
                term = get_object_or_404(Term, id=term)
            else:
                term = current_term
        except:
            return []

        for student in queryset:
            totalExpected = Decimal('0.0')
            totalPaid = Decimal('0.0')

            invoiceList = Invoice.objects.filter(term=term, year=year, student=student)
            if startdate:
                invoiceList = invoiceList.filter(issueDate__gt=startdate, issueDate__isnull=False)
            if enddate:
                invoiceList = invoiceList.filter(issueDate__lte=enddate, issueDate__isnull=False)
            totalExpected += invoiceList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')

            receiptList = Receipt.objects.filter(term=term, year=year, student=student, is_reversed=False)
            if startdate:
                receiptList = receiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                receiptList = receiptList.filter(receipt_date__lte=enddate, receipt_date__isnull=False)
            paid = receiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            pikReceiptList = PIKReceipt.objects.filter(term=term, year=year, student=student, is_posted=True)
            if startdate:
                pikReceiptList = pikReceiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                pikReceiptList = pikReceiptList.filter(receipt_date__lte=enddate, receipt_dte__isnull=False)
            paid = pikReceiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            bursaryItemList = Item.objects.filter(bursary__term=term, bursary__year=year, student=student,bursary__posted=True)

            if startdate:
                bursaryItemList = bursaryItemList.filter(item_date__gt=startdate, item_date__isnull=False)
            if enddate:
                bursaryItemList = bursaryItemList.filter(item_date__lte=enddate, item_date__isnull=False)
            paid = bursaryItemList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            boarding_status = None

            reportStudentBalance = ReportStudentBalance(
                admission_number=student.admission_number,
                name=f"{student.first_name} {student.last_name}",
                current_Class=student.current_Class,
                boarding_status=student.boarding_status,
                expected=totalExpected,
                paid=totalPaid,
                totalBalance=totalExpected - totalPaid,
                schoolFee=totalExpected
            )

            reportsStudentBalanceList.append(reportStudentBalance)

        return reportsStudentBalanceList

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            queryset = Student.objects.filter(school_id=school_id)

            currentClass = request.GET.get('currentClass')
            stream = request.GET.get('stream')
            student = request.GET.get('student')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')
            boardingstatus = request.GET.get('boardingstatus')
            amountabove = request.GET.get('amountabove')
            amountbelow = request.GET.get('amountbelow')
            term = request.GET.get('term')
            year = request.GET.get('year')

            reportsStudentBalanceList = []

            if not currentClass and not stream and not student:
                print("here")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if currentClass:
                queryset = queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if stream:
                # if not currentClass:
                # return Response({'detail': f"Both Class and Stream must be entered to query stream"},status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(current_Stream=stream)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if student:
                queryset = queryset.filter(id=student)
                print(f"student was passed {queryset}")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if amountbelow:
                amountbelow = Decimal(amountbelow)
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance < amountbelow]

            if amountabove:
                amountabove = Decimal(amountabove)
                print(f"Amount above was passed {reportsStudentBalanceList}")
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance > amountabove]

            print(f"Students List is {reportsStudentBalanceList}")
            serializer = ReportStudentBalanceSerializer(reportsStudentBalanceList, many=True)
            serialized_data = serializer.data
            return Response({'detail': serialized_data}, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class FilterStudents(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    model = Student

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        currentClass = request.GET.get('currentClass')
        currentStream = request.GET.get('currentStream')
        admissionNumber = request.GET.get('admissionNumber')
        studentid = request.GET.get('studentid')

        queryset = Student.objects.filter(school_id=school_id)

        try:

            if not currentClass or not currentStream or not admissionNumber:
                pass

            if studentid:
                queryset = queryset.filter(id = studentid)

            if admissionNumber:
                queryset = queryset.filter(admission_number = admissionNumber)

            if currentClass:
                queryset = queryset.filter(current_Class = currentClass)

            if currentStream:
                if not currentClass:
                    return Response({'detail': f"Please  student class"}, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(current_Stream = currentStream,  current_Class=currentClass)

            if not queryset:
                return JsonResponse([], status=200)

            for student in queryset:
                student.school_id = school_id

            serializer = StudentSerializer(queryset, many=True)
            serialized_data = serializer.data

            return Response({'detail': serialized_data}, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'detail': f"{exception}"}, status=status.HTTP_400_BAD_REQUEST)


class StudentTransactionsPrint(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.filter()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):

        try:
            student = self.get_object()

            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')
            term = request.GET.get('term')
            academicYear = request.GET.get('academicYear')

            querysetInvoices = Invoice.objects.filter(
                student_id=student.id,
                school_id=school_id
            )

            querysetReceipts = Receipt.objects.filter(
                student_id=student.id,
                school_id=school_id,
                is_reversed=False,
            )

            querysetPIKReceipts = PIKReceipt.objects.filter(
                is_posted=True,
                student_id=student.id,
                school_id=school_id
            )

            querysetBursaries = Item.objects.filter(
                student_id=student.id,
                school_id=school_id
            )

            if term:
                querysetInvoices = querysetInvoices.filter(term__id=term)
                querysetReceipts = querysetReceipts.filter(term__id=term)
                querysetPIKReceipts = querysetPIKReceipts.filter(term__id=term)
                querysetBursaries = querysetBursaries.filter(bursary__term__id=term)

            if academicYear:
                querysetInvoices = querysetInvoices.filter(year__id=academicYear)
                querysetReceipts = querysetReceipts.filter(year__id=academicYear)
                querysetPIKReceipts = querysetPIKReceipts.filter(year__id=academicYear)
                querysetBursaries = querysetBursaries.filter(bursary__year__id=academicYear)

            if startdate:
                querysetInvoices = querysetInvoices.filter(issueDate__gt = startdate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__gt = startdate, transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__gt = startdate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__gt = startdate, bursary__receipt_date__isnull=False)

            if enddate:
                querysetInvoices = querysetInvoices.filter(issueDate__lte = enddate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__lte = enddate,  transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__lte = enddate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__lte = enddate, bursary__receipt_date__isnull=False)

            studentTransactionList = []

            for value in querysetReceipts:
                term_name = getattr(value.term, 'term_name', None)
                year_name = getattr(value.year, 'academic_year', None)
                student_class = getattr(value, 'student_class', None)
                transaction_date = getattr(value, 'transaction_date', None)
                description = f"{student_class}-{term_name}-{year_name}"

                item = StudentTransactionsPrintView(
                    transactionDate=transaction_date,
                    transactionType="FEE COLLECTION",
                    description=description,
                    expected="",
                    paid=value.totalAmount
                )
                item.save()
                studentTransactionList.append(item)

            for value in querysetPIKReceipts:
                term_name = getattr(value.term, 'term_name', None)
                year_name = getattr(value.year, 'academic_year', None)
                student_class = getattr(value, 'student_class', None)
                transaction_date = getattr(value, 'receipt_date', None)
                description = f"{student_class}-{term_name}-{year_name}"

                item = StudentTransactionsPrintView(
                    transactionDate=transaction_date,
                    transactionType="PAYMENT IN KIND",
                    description=description,
                    expected="",
                    paid=value.totalAmount
                )
                item.save()
                studentTransactionList.append(item)

            for value in querysetBursaries:
                term_name = getattr(value.bursary.term, 'term_name', None)
                year_name = getattr(value.bursary.year, 'academic_year', None)
                student_class = getattr(value, 'student_class', None)
                transaction_date = getattr(value.bursary, 'receipt_date', None)
                description = f"{student_class}-{term_name}-{year_name}"

                item = StudentTransactionsPrintView(
                    transactionDate=transaction_date,
                    transactionType="BURSARY",
                    description=description,
                    expected="",
                    paid=value.amount
                )
                item.save()
                studentTransactionList.append(item)

            for value in querysetInvoices:
                term_name = getattr(value.term, 'term_name', None)
                year_name = getattr(value.year, 'academic_year', None)
                student_class = getattr(value, 'classes', None)
                transaction_date = getattr(value, 'issueDate', None)
                description = f"{student_class}-{term_name}-{year_name}"

                item = StudentTransactionsPrintView(
                    transactionDate=transaction_date,
                    transactionType="FEES INVOICE",
                    description=description,
                    expected=value.amount,
                    paid=""
                )
                item.save()
                studentTransactionList.append(item)

            for value in studentTransactionList:
                print(f"{value.transactionDate} - {value.transactionType}")

            def get_transaction_date(item):
                transaction_date = getattr(item, 'transactionDate', date.max)
                if isinstance(transaction_date, str):
                    transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()

                return transaction_date

            studentTransactionList = sorted(studentTransactionList, key=get_transaction_date)
            serializer = StudentTransactionsPrintViewSerializer(studentTransactionList, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})



class StudentCollectionListView(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):

        try:
            student = self.get_object()

            print(f"Student is {student}")

            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')
            term = request.GET.get('term')
            academicYear = request.GET.get('academicYear')

            queryset = Receipt.objects.filter(
                is_reversed = False,
                student_id=student.id,
                school_id=school_id
            )

            if term:
                queryset = queryset.filter(term__id=term)

            if academicYear:
                queryset = queryset.filter(year__id=academicYear)

            if startdate:
                queryset = queryset.filter(transaction_date__gt = startdate, transaction_date__isnull=False)

            if enddate:
                queryset = queryset.filter(transaction_date__lte = enddate,transaction_date__isnull=False)

            serializer = ReceiptSerializer(queryset, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})


class IncomeSummaryView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):


        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            querysetCollections = Collection.objects.filter(
                receipt__is_reversed = False,
                school_id=school_id
            )

            querysetPIK = PaymentInKind.objects.filter(
                receipt__is_posted = True,
                school_id=school_id
            )

            if not orderby or not accounttype:
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetCollections = querysetCollections.filter(receipt__account_type__id=accounttype)
            querysetPIK = querysetPIK.filter(receipt__bank_account__account_type__id = accounttype)

            if startdate:
                querysetCollections = querysetCollections.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
            if enddate:
                querysetCollections = querysetCollections.filter(transaction_date__lte=enddate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__lte=enddate, transaction_date__isnull=False)

            incomeSummaryList = []


            paymentMethods = PaymentMethod.objects.filter(school__id = school_id)

            if orderby == "paymentmode":
                for paymentmode in paymentMethods:
                    totalAmount = Decimal('0.0')
                    paymentmode_name = paymentmode.name

                    for collection in querysetCollections:
                        if collection.receipt.payment_method == paymentmode:
                            totalAmount += collection.amount

                    for pik in querysetPIK:
                        if pik.receipt.payment_method == paymentmode:
                            totalAmount += pik.amount

                    item = IncomeSummary(
                        votehead_name=paymentmode_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)


            voteheads = VoteHead.objects.all()
            if orderby == "votehead":
                for votehead in voteheads:
                    totalAmount = Decimal('0.0')
                    votehead_name = votehead.vote_head_name

                    for collection in querysetCollections:
                        if collection.votehead == votehead:
                            totalAmount += collection.amount

                    for pik in querysetPIK:
                        if pik.votehead == votehead:
                            totalAmount += pik.amount

                    item = IncomeSummary(
                        votehead_name=votehead_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)

            serializer = IncomeSummarySerializer(incomeSummaryList, many=True)

            grandTotal = Decimal('0.0')
            for income_summary in incomeSummaryList:
                print(f'Type of income_summary.amount: {type(income_summary.amount)}')
                print(f'Type of grandTotal before addition: {type(grandTotal)}')
                grandTotal += income_summary.amount

            thedata = {
                'summary': serializer.data,
                'grandtotal': grandTotal
            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})


class ExpenseSummaryView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            querysetExpenses = Voucher.objects.filter(
                is_deleted=False,
                school_id=school_id
            )

            if not orderby or not accounttype:
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetExpenses = querysetExpenses.filter(bank_account__account_type__id=accounttype)

            if startdate:
                querysetExpenses = querysetExpenses.filter(paymentDate__gt=startdate, paymentDate__isnull=False)
            if enddate:
                querysetExpenses = querysetExpenses.filter(paymentDate__lte=enddate, paymentDate__isnull=False)


            incomeSummaryList = []

            paymentMethods = PaymentMethod.objects.filter(school__id = school_id)

            if orderby == "paymentmode":
                for paymentmode in paymentMethods:
                    totalAmount = Decimal('0.0')
                    paymentmode_name = paymentmode.name

                    for voucher in querysetExpenses:
                        for expense in voucher.voucher_items.all():
                            if expense.voucher.payment_Method == paymentmode:
                                totalAmount += expense.amount

                    item = IncomeSummary(
                        votehead_name=paymentmode_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)


            voteheads = VoteHead.objects.all()
            if orderby == "votehead":
                for votehead in voteheads:
                    totalAmount = Decimal('0.0')
                    votehead_name = votehead.vote_head_name

                    for voucher in querysetExpenses:
                        for expense in voucher.voucher_items.all():
                            if expense.votehead == votehead:
                                totalAmount += expense.amount

                    item = IncomeSummary(
                        votehead_name=votehead_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)

            serializer = IncomeSummarySerializer(incomeSummaryList, many=True)

            grandTotal = Decimal('0.0')
            for expense_summary in incomeSummaryList:
                print(f'Type of expense_summary.amount: {type(expense_summary.amount)}')
                print(f'Type of grandTotal before addition: {type(grandTotal)}')
                grandTotal += expense_summary.amount

            thedata = {
                'summary': serializer.data,
                'grandtotal': grandTotal
            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})





class ReceivedChequesView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            querysetCollections = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                receipt__payment_method__is_cheque=True
            )

            chequeCollectionList = []
            for collection in querysetCollections:
                creationdate = collection.receipt.dateofcreation
                transactiondate = collection.receipt.transaction_date
                chequeNo = collection.receipt.transaction_code
                student = collection.student
                currency = collection.receipt.currency
                amount = collection.amount

                item = ReceivedCheque(
                    transactionDate=transactiondate,
                    dateofcreation=creationdate,
                    chequeNo=chequeNo,
                    student=student,
                    currency=currency,
                    amount=amount
                )
                item.save()
                chequeCollectionList.append(item)

            serializer = ReceivedChequeSerializer(chequeCollectionList, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})









class CashBookView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            bankaccount = request.GET.get('bankaccount')
            accounttype = request.GET.get('accounttype')
            financialyear = request.GET.get('financialyear')
            month = request.GET.get('month')

            querySetReceipts = Receipt.objects.filter(school_id=school_id, is_reversed = False)
            querysetPIK = PIKReceipt.objects.filter(school_id=school_id, is_posted=True)
            querySetExpenses = VoucherItem.objects.filter(school_id=school_id, voucher__is_deleted=False)

            if bankaccount and bankaccount != "":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, bank_account__id = bankaccount)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__id = bankaccount)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__bank_account__id = bankaccount)

            if accounttype and accounttype != "":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, account_type__id=accounttype)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__account_type__id=accounttype)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__bank_account__account_type__id=accounttype)
            else:
                return Response({'detail': f"Account Type is required"}, status=status.HTTP_400_BAD_REQUEST)

            if financialyear and financialyear != "":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
                querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__financial_year__id=financialyear)

            if month and month != "":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, transaction_date__month=month)
                querysetPIK = querysetPIK.filter(school_id=school_id, receipt_date__month=month)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__paymentDate__month=month)

            # if not bankaccount or not accounttype:
            #     return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            listofdateofcreations = []
            listofdateofcreations.extend(querySetReceipts.values_list('transaction_date', flat=True))
            listofdateofcreations.extend(querysetPIK.values_list('receipt_date', flat=True))
            listofdateofcreations = list(set(listofdateofcreations))
            listofdateofcreations = list(listofdateofcreations)

            listofreceipts = []
            universalvoteheadDictionary_collection_voteheads = {}

            total_receipt_cash = Decimal(0.0)
            total_receipt_bank = Decimal(0.0)

            total_expenses_cash = Decimal(0.0)
            total_expenses_bank = Decimal(0.0)

            if not month:
                opening_balance = Decimal(0.0)
                opencash = Decimal(0.0)
                openbank = Decimal(0.0)
            else:
                opencash = getBalance(accounttype, month, financialyear, school_id)["cash"]
                openbank = getBalance(accounttype, month, financialyear, school_id)["bank"]

            for dateinstance in listofdateofcreations:
                receipt_range = []
                total_amount = Decimal("0.0")
                cash = Decimal(opencash)
                bank = Decimal(openbank)
                inkind = Decimal("0.0")
                voteheadDictionary = {}
                for receipt in querySetReceipts:
                    if receipt.transaction_date == dateinstance:
                        method = "NONE"
                        if receipt.payment_method:
                            method = "BANK" if receipt.payment_method.is_cheque else "CASH" if receipt.payment_method.is_cash else "BANK" if receipt.payment_method.is_bank else "NONE"
                        if method == "CASH":
                            cash += Decimal(receipt.totalAmount)
                        if method == "BANK":
                            bank += Decimal(receipt.totalAmount)
                        if method == "NONE":
                            inkind += Decimal(receipt.totalAmount)

                        counter = receipt.counter
                        amount = Decimal(receipt.totalAmount)
                        receipt_range.append(counter)
                        total_amount += amount
                        if "total_amount" not in universalvoteheadDictionary_collection_voteheads:
                            universalvoteheadDictionary_collection_voteheads[f"total_amount"] = Decimal(amount)
                        else:
                            universalvoteheadDictionary_collection_voteheads[f"total_amount"] += Decimal(amount)

                    collections = Collection.objects.filter(receipt=receipt)
                    for collection in collections:
                        if collection.votehead.vote_head_name not in voteheadDictionary:
                            voteheadDictionary[f"{collection.votehead.vote_head_name}"] = Decimal(collection.amount)
                        else:
                            voteheadDictionary[f"{collection.votehead.vote_head_name}"] += Decimal(collection.amount)

                        if collection.votehead.vote_head_name not in universalvoteheadDictionary_collection_voteheads:
                            universalvoteheadDictionary_collection_voteheads[f"{collection.votehead.vote_head_name}"] = Decimal(collection.amount)
                        else:
                            universalvoteheadDictionary_collection_voteheads[f"{collection.votehead.vote_head_name}"] += Decimal(collection.amount)



                for pikreceipt in querysetPIK:
                    if pikreceipt.receipt_date == dateinstance:
                        inkind += Decimal(pikreceipt.totalAmount)
                        counter = pikreceipt.counter
                        amount = Decimal(pikreceipt.totalAmount)
                        receipt_range.append(counter)
                        total_amount += amount

                    piks = PaymentInKind.objects.filter(receipt=pikreceipt)
                    for pik in piks:
                        if pik.votehead.vote_head_name not in voteheadDictionary:
                            voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                        else:
                            voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
                        if pik.votehead.vote_head_name not in universalvoteheadDictionary_collection_voteheads:
                            universalvoteheadDictionary_collection_voteheads[f"{pik.votehead.vote_head_name}"] = pik.amount
                        else:
                            universalvoteheadDictionary_collection_voteheads[f"{pik.votehead.vote_head_name}"] += pik.amount


                result = ""
                if receipt_range:
                    print(f"Receipt range is {receipt_range}")
                    result = f"{min(receipt_range)} - {max(receipt_range)}"

                print(f"Total amount for date {dateinstance}: {total_amount}")
                print(f"voteheadDictionary for date {dateinstance}: {voteheadDictionary}")

                total_receipt_cash += cash
                total_receipt_bank += bank

                listofreceipts.append(
                    {
                        "date" : dateinstance,
                        "description": "Income",
                        "receipt_range": result,
                        "cash": cash,
                        "bank": bank,
                        "inkind": inkind,
                        "total_amount": total_amount,
                        "voteheads": voteheadDictionary,
                        "summary": universalvoteheadDictionary_collection_voteheads,
                    }
                )

            #EXPENSES OR VOUCHERS
            listofVoucherDateCreations = []
            listofVoucherDateCreations.extend(querySetExpenses.values_list('voucher__paymentDate', flat=True))
            listofVoucherDateCreations = list(set(listofVoucherDateCreations))
            listofVoucherDateCreations = list(listofVoucherDateCreations)

            listofVouchers = []
            universalvoteheadDictionary_payment_voteheads = {}

            for dateinstance in listofVoucherDateCreations:
                receipt_range = []
                total_amount = Decimal("0.0")
                cash = Decimal("0.0")
                bank = Decimal("0.0")
                voteheadDictionary = {}
                for voucher in querySetExpenses:
                    if voucher.voucher.paymentDate == dateinstance:
                        method = "BANK" if voucher.voucher.payment_Method.is_cheque else "CASH" if voucher.voucher.payment_Method.is_cash else "BANK" if voucher.voucher.payment_Method.is_bank else "NONE"
                        if method == "CASH":
                            cash += Decimal(voucher.amount)
                        if method == "BANK":
                            bank += Decimal(voucher.amount)
                        if method == "NONE":
                            cash += Decimal(voucher.amount)

                        counter = voucher.voucher.counter
                        amount = Decimal(voucher.amount)
                        receipt_range.append(counter)
                        total_amount += amount
                        if "total_amount" not in universalvoteheadDictionary_payment_voteheads:
                            universalvoteheadDictionary_payment_voteheads[f"total_amount"] = Decimal(amount)
                        else:
                            universalvoteheadDictionary_payment_voteheads[f"total_amount"] += Decimal(amount)


                        if voucher.votehead.vote_head_name not in voteheadDictionary:
                            voteheadDictionary[f"{voucher.votehead.vote_head_name}"] = Decimal(voucher.amount)
                        else:
                            voteheadDictionary[f"{voucher.votehead.vote_head_name}"] += Decimal(voucher.amount)

                        if voucher.votehead.vote_head_name not in universalvoteheadDictionary_payment_voteheads:
                            universalvoteheadDictionary_payment_voteheads[f"{voucher.votehead.vote_head_name}"] = Decimal(voucher.amount)
                        else:
                            universalvoteheadDictionary_payment_voteheads[f"{voucher.votehead.vote_head_name}"] += Decimal(voucher.amount)

                total_expenses_cash += cash
                total_expenses_bank += bank

                result = ""
                if receipt_range:
                    result = f"{min(receipt_range)} - {max(receipt_range)}"

                listofVouchers.append(
                    {
                        "date": dateinstance,
                        "description": "Expense",
                        "receipt_range": result,
                        "cash": cash,
                        "bank": bank,
                        "total_amount": total_amount,
                        "voteheads": voteheadDictionary,
                    }
                )

            if not month:
                total_opening_balance = Decimal(0.0)
                opening_cash = Decimal(0.0)
                opening_bank = Decimal(0.0)
            else:
                total_opening_balance = getBalance(accounttype, month, financialyear, school_id)["total"]
                opening_cash = getBalance(accounttype, month, financialyear, school_id)["cash"]
                opening_bank = getBalance(accounttype, month, financialyear, school_id)["bank"]

            total_expense = sum(voucher.get("total_amount", 0) for voucher in listofVouchers)
            total_collection = sum(collection.get("total_amount", 0) for collection in listofreceipts)
            total_collectioncash = sum(collection.get("cash", 0) for collection in listofreceipts)
            total_collectionbank = sum(collection.get("bank", 0) for collection in listofreceipts)

            total_expensecash = sum(collection.get("cash", 0) for collection in listofVouchers)
            total_expensebank = sum(collection.get("bank", 0) for collection in listofVouchers)

            total_total_expense =  Decimal(total_expensecash) + Decimal(total_expensebank),

            total_total_collection = Decimal(total_collectioncash) + Decimal(total_collectionbank)
            total_closing_balance = (Decimal(total_opening_balance) + Decimal(total_total_collection)) - Decimal(total_expense)

            closing_cash = Decimal(opening_cash) + Decimal(total_collectioncash) - Decimal(total_expensecash)
            closing_bank = Decimal(opening_cash) + Decimal(total_collectionbank) - Decimal(total_expensebank)

            thedata = {

                "receipts" : listofreceipts,
                "payments": listofVouchers,

                "opening_cash": opening_cash,
                "opening_bank": opening_bank,
                "total_opening_balance": total_opening_balance,

                "total_expense": total_total_expense,
                "total_collection": total_collection,

                "closing_cash": closing_cash,
                "closing_bank": closing_bank,
                "total_closing_balance": total_closing_balance,

                "total_collectioncash": total_collectioncash,
                "total_collectionbank": total_collectionbank,
                "total_total_collection": total_total_collection,

                "total_expensecash": total_expensecash,
                "total_expensebank": total_expensebank,
                "total_total_expense": total_total_expense,

                "total_payment_voteheads": universalvoteheadDictionary_payment_voteheads,
                "total_collection_voteheads": universalvoteheadDictionary_collection_voteheads,

            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})





class FeeRegisterView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            student = request.GET.get('student')
            financialyear = request.GET.get('financialyear')
            academicyear = request.GET.get('academicyear')
            classes = request.GET.get('classes')
            stream = request.GET.get('stream')

            if not student and not classes and not stream:
                return Response({'detail': f"Either of Student or Stream or Class should be passed"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                student = Student.objects.get(id=student, school_id=school_id)
            except ObjectDoesNotExist:
                return Response({'detail': f"Invalid Student"}, status=status.HTTP_400_BAD_REQUEST)

            student_List = []
            if student:
                student_List.append(student)

            if classes:
                class_students = Student.objects.filter(school_id=school_id, current_Class__id = classes)
                if class_students:
                    for value in class_students:
                        student_List.append(value)

            if stream:
                stream_students = Student.objects.filter(current_Stream__id=stream, school_id=school_id)
                if stream_students:
                    for value in stream_students:
                        student_List.append(value)

            student_final_output = []

            for student in student_List:
                student_name = f"{student.first_name} - {student.last_name}"
                student_admission = student.admission_number
                student_class = student.current_Class
                student_stream = student.current_Stream

                querySetReceipts = Receipt.objects.filter(school_id=school_id, student=student, is_reversed = False)
                querysetPIK = PIKReceipt.objects.filter(school_id=school_id, student=student, is_posted=True)

                if financialyear:
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)

                if academicyear:
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, year__id = academicyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, year__id = academicyear)


                listofdateofcreations = []
                listofdateofcreations.extend(querySetReceipts.values_list('transaction_date', flat=True))
                listofdateofcreations.extend(querysetPIK.values_list('receipt_date', flat=True))
                listofdateofcreations = list(set(listofdateofcreations))
                listofdateofcreations = list(listofdateofcreations)

                listofreceipts = []
                universalvoteheadDictionary = {}


                dated_instances = []

                for dateinstance in listofdateofcreations:

                    receipts = []

                    for receipt in querySetReceipts:
                        voteheadDictionary = {}
                        if receipt.transaction_date == dateinstance:
                            receipt_number = receipt.receipt_No
                            balance_before = "0.0"
                            amount_paid = "0.0"
                            balance_after = "0.0"

                            balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
                            if balanceTrackerQuerySet:
                                balance_before = balanceTrackerQuerySet.balanceBefore
                                balance_after = balanceTrackerQuerySet.balanceAfter
                                amount_paid = balanceTrackerQuerySet.amountPaid

                            receiptsList = Collection.objects.filter(receipt=receipt)
                            for collection in receiptsList:
                                if collection.votehead.vote_head_name not in voteheadDictionary:
                                    voteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
                                else:
                                    voteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount
                                if collection.votehead.vote_head_name not in universalvoteheadDictionary:
                                    universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
                                else:
                                    universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount

                            receiptObject = {
                                "date": dateinstance,
                                "receipt_number": receipt_number,
                                "balance_before": balance_before,
                                "balance_after": balance_after,
                                "transaction_amount": amount_paid,
                                "voteheads": voteheadDictionary,
                            }

                            receipts.append(receiptObject)

                    for pik in querysetPIK:
                        voteheadDictionary = {}
                        if pik.receipt_date == dateinstance:
                            receipt_number = pik.receipt_No
                            balance_before = "0.0"
                            amount_paid = "0.0"
                            balance_after = "0.0"

                            balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
                            if balanceTrackerQuerySet:
                                balance_before = balanceTrackerQuerySet.balanceBefore
                                balance_after = balanceTrackerQuerySet.balanceAfter
                                amount_paid = balanceTrackerQuerySet.amountPaid

                            piks = PaymentInKind.objects.filter(receipt=pik)
                            for pik in piks:
                                if pik.votehead.vote_head_name not in voteheadDictionary:
                                    voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                                else:
                                    voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
                                if pik.votehead.vote_head_name not in universalvoteheadDictionary:
                                    universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                                else:
                                    universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount

                            receiptObject = {
                                "date": dateinstance,
                                "receipt_number": receipt_number,
                                "balance_before": balance_before,
                                "balance_after": balance_after,
                                "transaction_amount": amount_paid,
                                "voteheads": voteheadDictionary,
                            }
                            receipts.append(receiptObject)


                    output = {
                        "date": dateinstance,
                        "receipts": receipts,
                    }

                    dated_instances.append(output)


                student_final_output.append(
                    {
                        "dated_student_instances": dated_instances,
                        "student": StudentSerializer(student).data,
                        "totals": universalvoteheadDictionary
                    }
                )

            thedata = student_final_output

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})






def getMonthly_Balances(month, school_Id):
    themonth = month - 1

    collectionsAmount = Collection.objects.filter(receipt__is_reversed=False, transaction_date__month=themonth, school_id = school_Id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    piksAmount = PaymentInKind.objects.filter(receipt__is_posted = True, transaction_date__month=themonth,school_id = school_Id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    expensesAmount = Voucher.objects.filter(is_deleted=False, paymentDate__month=themonth,school_id = school_Id).aggregate(Sum('totalAmount'))['totalAmount__sum'] or Decimal(0.0)

    totalCollections = Decimal(collectionsAmount) + Decimal(piksAmount)
    totalExpenses = Decimal(expensesAmount)

    return {
        "totalCollections": totalCollections,
        "totalExpenses": totalExpenses,
    }



class LedgerView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            financialyear = request.GET.get('financialyear')
            votehead = request.GET.get('votehead')

            if not financialyear or financialyear == "" or not votehead:
                return Response({'detail': f"Both financial year and votehead are required"}, status=status.HTTP_400_BAD_REQUEST)

            check_if_object_exists(VoteHead, votehead)
            check_if_object_exists(FinancialYear, financialyear)

            collectionQuerySet = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                receipt__financial_year__id=financialyear
            )

            pikQuerySet = PaymentInKind.objects.filter(
                receipt__is_posted=True,
                school_id=school_id,
                receipt__financial_year__id=financialyear
            )

            voucherQuerySet = Voucher.objects.filter(
                is_deleted=False,
                school_id=school_id,
                financial_year__id=financialyear
            )

            collectionQuerySet = collectionQuerySet if collectionQuerySet.exists() else Collection.objects.none()
            pikQuerySet = pikQuerySet if pikQuerySet.exists() else PaymentInKind.objects.none()
            voucherQuerySet = voucherQuerySet if voucherQuerySet.exists() else Voucher.objects.none()

            print(f"{len(collectionQuerySet)}")
            print(f"{len(pikQuerySet)}")
            print(f"{len(voucherQuerySet)}")

            date_list = []

            unique_collection_dates = collectionQuerySet.values_list('transaction_date', flat=True).distinct()
            unique_pik_dates = pikQuerySet.values_list('transaction_date', flat=True).distinct()
            unique_voucher_dates = voucherQuerySet.values_list('paymentDate', flat=True).distinct()

            date_list.extend(unique_collection_dates)
            date_list.extend(unique_pik_dates)
            date_list.extend(unique_voucher_dates)

            date_list = list(set(date_list))

            actualFinancialYear = FinancialYear.objects.get(id = financialyear)
            monthlist  = FinancialYear.get_month_info(actualFinancialYear)

            print(f"{monthlist}")

            response_object = []

            for position, month in enumerate(monthlist):
                startdate = month['start_date']
                enddate = month['end_date']
                monthnumber = month['month_number']

                total_month_collection_amount = Decimal(0.0)

                for collection in collectionQuerySet:
                    if str(collection.votehead.id) == votehead:
                        if collection.transaction_date.month == monthnumber:
                            collection_amount = collection.amount
                            total_month_collection_amount += collection_amount

                for pik in pikQuerySet:
                    if str(pik.votehead.id) == votehead:
                        if pik.transaction_date.month == monthnumber:
                            pik_amount = pik.amount
                            total_month_collection_amount += pik_amount

                total_month_expenses_amount = Decimal(0.0)


                for voucher in voucherQuerySet:
                    items = VoucherItem.objects.filter(school_id = school_id)
                    for item in items:
                        if item.voucher == voucher:
                            print(f"Item voucher is same. Item votehead is {str(item.votehead.id)} and votehead sent is {votehead}")
                            if str(item.votehead.id) == votehead:
                                print(f"Voteheads are the same")
                                if item.voucher.paymentDate.month == monthnumber:
                                    print(f"Item voucher month is same as month in search")
                                    item_amount = item.amount
                                    total_month_expenses_amount += item_amount

                if position == 0:
                    previous_total_cr = total_month_collection_amount
                    previous_total_dr = total_month_expenses_amount
                else:
                    previous_month_balances = getMonthly_Balances(monthnumber, school_id)
                    previous_total_cr = previous_month_balances['totalCollections']
                    previous_total_dr = previous_month_balances['totalExpenses']

                response_object.append({
                    "start_date": startdate,
                    "month": monthnumber,
                    "cr": total_month_collection_amount,
                    "dr": total_month_expenses_amount,
                    "previous_total_cr": previous_total_cr,
                    "previous_total_dr": previous_total_dr
                })

            thedata = response_object
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})









class TrialBalanceView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        financialyear = request.GET.get('financialyear')
        accounttype = request.GET.get('accounttype')
        month = request.GET.get('month')

        if not financialyear or financialyear=="" or not accounttype or accounttype == "" or not month or month == "":
            return Response({'detail': f"Account Type, Financial Year and Month are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            openingObject = OpeningClosingBalances.objects.get(school_id=school_id, financial_year__id=financialyear)
        except OpeningClosingBalances.DoesNotExist:
            openingObject = None

        cash_at_hand  = Decimal(0.0)
        cash_at_bank  = Decimal(0.0)

        if openingObject:
            cash_at_hand = openingObject.opening_cash_at_hand
            cash_at_bank = openingObject.opening_cash_at_bank

        votehead_list = VoteHead.objects.filter(school_id=school_id)

        print(f"Votehead list is {votehead_list}")
        collectionvoteheadDictionary = {}

        total_cash = Decimal(0.0)
        total_bank = Decimal(0.0)
        total_expense = Decimal(0.0)

        for votehead in votehead_list:

            piks = PaymentInKind.objects.filter(
                receipt__is_posted=True,
                school_id=school_id,
                receipt__financial_year=financialyear,
                transaction_date__month__lte=month
            )

            print(f"pik {len(piks)}")

            for pik in piks:
                votehead_id = pik.votehead.id

                if not collectionvoteheadDictionary.get(votehead_id):
                    collectionvoteheadDictionary[votehead_id] = {
                        "vote_head_name": pik.votehead.vote_head_name,
                        "cramount": Decimal(0.0),
                        "lf_number": pik.votehead.ledget_folio_number_lf
                    }
                if pik.votehead == votehead:
                    total_cash += pik.amount
                    print(f"Before accessing 'cramount' for {votehead_id}: {collectionvoteheadDictionary.get(votehead_id)}")
                    if 'cramount' not in collectionvoteheadDictionary[votehead_id]:
                        collectionvoteheadDictionary[votehead_id]['cramount'] = Decimal(0.0)

                    collectionvoteheadDictionary[votehead_id]['cramount'] += pik.amount

            collections = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                receipt__financial_year=financialyear,
                transaction_date__month__lte=month
            )

            print(f"{school_id}")
            print(f"Collections {len(collections)}")


            for collection in collections:
                votehead_id = collection.votehead.id

                if not collectionvoteheadDictionary.get(votehead_id):
                    print(f"Creating dictionary for votehead_id: {votehead_id}")
                    print(f"Creating dictionary for votehead_id: {votehead_id}")
                    collectionvoteheadDictionary[votehead_id] = {
                        "vote_head_name": collection.votehead.vote_head_name,
                        "cramount": Decimal(0.0),
                        "lf_number": collection.votehead.ledget_folio_number_lf
                    }

                if collection.votehead == votehead:
                    receipt = collection.receipt
                    method = "NONE"
                    if receipt.payment_method:
                        method = "BANK" if receipt.payment_method.is_cheque else "CASH" if receipt.payment_method.is_cash else "BANK" if receipt.payment_method.is_bank else "NONE"
                    if method == "CASH":
                        total_cash += Decimal(collection.amount)
                    if method == "BANK":
                        total_bank += Decimal(collection.amount)
                    if method == "NONE":
                        total_cash += Decimal(collection.amount)

                    print(f"Updating dictionary for votehead_id: {votehead_id}")
                    collectionvoteheadDictionary[votehead_id]["cramount"] += collection.amount



            expenses = VoucherItem.objects.filter(
                voucher__is_deleted=False,
                school_id=school_id,
                voucher__financial_year=financialyear,
                voucher__paymentDate__month__lte=month
            )

            print(f"{expenses}")



            for voucher_item in expenses:
                votehead_id = voucher_item.votehead.id

                if not collectionvoteheadDictionary.get(votehead_id):
                    print(f"Creating dictionary for votehead_id: {votehead_id}")
                    print(f"Creating dictionary for votehead_id: {votehead_id}")
                    collectionvoteheadDictionary[votehead_id] = {
                        "vote_head_name": voucher_item.votehead.vote_head_name,
                        "dramount": Decimal(0.0),
                        "lf_number": voucher_item.votehead.ledget_folio_number_lf
                    }
                if voucher_item.votehead == votehead:
                    total_expense += Decimal(voucher_item.amount)

                    collectionvoteheadDictionary[voucher_item.votehead.id]["dramount"] += voucher_item.amount


        overall_total = Decimal(cash_at_hand) + Decimal(cash_at_bank) + Decimal(total_cash) + Decimal(total_bank)

        collection_voteheads_list = [
            {
                "votehead": votehead,
                "cramount": data["cramount"],
                "dramount": data["dramount"],
                "lf_number": data["lf_number"]
            }
            for votehead, data in collectionvoteheadDictionary.items()
        ]


        save_object = {
            "cash_at_hand": cash_at_hand,
            "cash_at_bank": cash_at_bank,
            "voteheads": collection_voteheads_list,
            "closing_cash": total_cash,
            "closing_bank": total_bank,
            "overall_total": overall_total
        }

        return Response({"detail": save_object})









class NotesView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        financialyear = request.GET.get('financialyear')

        if not financialyear or financialyear=="":
            return Response({'detail': f"Financial Year is required"}, status=status.HTTP_400_BAD_REQUEST)

        accountTypeList = AccountType.objects.filter(school_id=school_id) or []
        votehead_list = VoteHead.objects.filter(school_id=school_id)




        try:
            current_financial_year = FinancialYear.objects.get(school_id = school_id, is_current = True)
        except ObjectDoesNotExist:
            return Response({'detail': f"Current financial year has not been set for this school"}, status=status.HTTP_400_BAD_REQUEST)

        financial_year_list = FinancialYear.objects.filter(school_id=school_id).order_by('dateofcreation')
        current_financial_year_index = financial_year_list.index(current_financial_year)
        if current_financial_year_index > 0:
            previous_year = financial_year_list[current_financial_year_index - 1]
        else:
            previous_year = None


        collections_list = []
        expenses_list = []
        my_bank_account_list = []
        cash_in_hand_list = []


        #COLLECTIONS
        for accountType in accountTypeList:
            accountype_name  = accountType.account_type_name

            collection_votehead = {}
            current_collection_total = Decimal(0.0)
            previous_collection_total = Decimal(0.0)

            #COLLECTION - COLLECTIONS
            current_collections = Receipt.objects.filter(school_id = school_id, is_reversed = False, account_type = accountType, financial_year__id = financialyear) or []
            for collection in current_collections:
                amount = collection.totalAmount
                for votehead in votehead_list:
                    votehead_name = votehead.vote_head_name
                    if not collection_votehead.get(votehead_name):
                        collection_votehead[votehead_name]["name"] = votehead_name
                        collection_votehead[votehead_name]["amount"] = Decimal(amount)
                        current_collection_total += Decimal(amount)
                    else:
                        collection_votehead[votehead_name]["amount"] += Decimal(amount)
                        current_collection_total += Decimal(amount)

            if previous_year:
                previous_year_collections = Receipt.objects.filter(school_id=school_id, is_reversed = False, account_type = accountType, financial_year = previous_year) or []
                for collection in previous_year_collections:
                    amount = collection.totalAmount
                    for votehead in votehead_list:
                        votehead_name = votehead.vote_head_name
                        if not collection_votehead.get(votehead_name):
                            collection_votehead[votehead_name]["name"] = votehead_name
                            collection_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                            previous_collection_total += Decimal(amount)

                        else:
                            collection_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                            previous_collection_total += Decimal(amount)

            #COLLECTION - PIKS
            current_PIKS = PIKReceipt.objects.filter(is_posted=True, school_id=school_id,
                                                         bank_account__account_type=accountType,
                                                         financial_year__id=financialyear) or []
            for pik in current_PIKS:
                amount = pik.totalAmount
                for votehead in votehead_list:
                    votehead_name = votehead.vote_head_name
                    if not collection_votehead.get(votehead_name):
                        collection_votehead[votehead_name]["name"] = votehead_name
                        collection_votehead[votehead_name]["amount"] = Decimal(amount)
                        current_collection_total += Decimal(amount)
                    else:
                        collection_votehead[votehead_name]["amount"] += Decimal(amount)
                        current_collection_total += Decimal(amount)

            if previous_year:
                previous_year_piks = PIKReceipt.objects.filter(account_type=accountType, school_id=school_id,
                                                                   financial_year=previous_year) or []
                for pik in previous_year_piks:
                    amount = pik.totalAmount
                    for votehead in votehead_list:
                        votehead_name = votehead.vote_head_name
                        if not collection_votehead.get(votehead_name):
                            collection_votehead[votehead_name]["name"] = votehead_name
                            collection_votehead[votehead_name]["amount"] = Decimal(amount)
                            previous_collection_total += Decimal(amount)
                        else:
                            collection_votehead[votehead_name]["amount"] += Decimal(amount)
                            previous_collection_total += Decimal(amount)

            send = {
                "account_type_name" : accountype_name,
                "current_collection_total": current_collection_total,
                "previous_collection_total" : previous_collection_total,
                "collection_votehead" : collection_votehead,
            }
            collections_list.append(send)



        #EXPENSES
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name
            expenses_votehead = {}
            current_expenses_total = Decimal(0.0)
            previous_expenses_total = Decimal(0.0)

            current_expenses = Voucher.objects.filter(is_deleted=False, school_id = school_id, bank_account__account_type = accountType, financial_year__id = financialyear) or []
            for expense in current_expenses:
                amount = expense.totalAmount
                for votehead in votehead_list:
                    votehead_name = votehead.vote_head_name
                    if not expenses_votehead.get(votehead_name):
                        expenses_votehead[votehead_name]["name"] = votehead_name
                        expenses_votehead[votehead_name]["amount"] = Decimal(amount)
                        current_expenses_total += Decimal(amount)
                    else:
                        expenses_votehead[votehead_name]["amount"] += Decimal(amount)
                        current_expenses_total += Decimal(amount)

            if previous_year:
                previous_year_expenses = Voucher.objects.filter(is_deleted=False, account_type = accountType, school_id = school_id, financial_year = previous_year) or []
                for expense in previous_year_expenses:
                    amount = expense.totalAmount
                    for votehead in votehead_list:
                        votehead_name = votehead.vote_head_name
                        if not expenses_votehead.get(votehead_name):
                            expenses_votehead[votehead_name]["name"] = votehead_name
                            expenses_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                            previous_expenses_total += Decimal(amount)

                        else:
                            expenses_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                            previous_expenses_total += Decimal(amount)

                send = {
                    "account_type_name": accountype_name,
                    "current_expenses_total": current_expenses_total,
                    "previous_expenses_total": previous_expenses_total,
                    "expenses_votehead": expenses_votehead,
                }
                expenses_list.append(send)



        #BANK ACCOUNTS
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name
            current_bank_total = Decimal(0.0)
            previous_bank_total = Decimal(0.0)

            small = []
            bank_account_list = BankAccount.objects.filter(school=school_id) or []

            for bank_account in bank_account_list:
                bank_account_name = bank_account.account_name
                bank_account_number = bank_account.account_number
                bank_account_currency = bank_account.currency

                receiptsQuerySet = Receipt.objects.filter(
                    account_type=accountType,
                    bank_account=bank_account,
                    financial_year=financialyear
                ).aggregate(result=Sum('totalAmount'))

                receipt_amount_sum = receiptsQuerySet.get('result', Decimal('0.0')) if receiptsQuerySet is not None else Decimal('0.0')

                pikQuerySet = PIKReceipt.objects.filter(
                    bank_account__account_type=accountType,
                    bank_account=bank_account,
                    financial_year=financialyear
                ).aggregate(result=Sum('totalAmount'))

                pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet is not None else Decimal('0.0')
                current_bank_total =  Decimal(receipt_amount_sum) +  Decimal(pik_receipt_sum)


                if previous_year:
                    receiptsQuerySet = Receipt.objects.filter(
                        account_type=accountType,
                        bank_account=bank_account,
                        financial_year=previous_year
                    ).aggregate(result=Sum('totalAmount'))

                    receipt_amount_sum = receiptsQuerySet.get('result', Decimal(
                        '0.0')) if receiptsQuerySet is not None else Decimal('0.0')

                    pikQuerySet = PIKReceipt.objects.filter(
                        bank_account__account_type=accountType,
                        bank_account=bank_account,
                        financial_year=previous_year
                    ).aggregate(result=Sum('totalAmount'))

                    pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet is not None else Decimal('0.0')
                    previous_bank_total = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)


                    send = {
                            "account_type_name": accountype_name,
                            "bank_account_name": bank_account_name,
                            "bank_account_number": bank_account_number,
                            "bank_account_currency": bank_account_currency,
                            "current_bank_total": current_bank_total,
                            "previous_bank_total": previous_bank_total,
                        }
                    my_bank_account_list.append(send)




        #CASH IN HAND
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name

            current_cash_in_hand = getBalancesByAccount(accountType, financialyear, school_id)['cash']
            previous_cash_in_hand = getBalancesByAccount(accountType, previous_year, school_id)['cash']

            send = {
                    "account_type_name": accountype_name,
                    "current_cash_in_hand": current_cash_in_hand,
                    "previous_cash_in_hand": previous_cash_in_hand,
                }

            cash_in_hand_list.append(send)




        #FINANCIAL
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name
            expenses_votehead = {}
            current_expenses_total = Decimal(0.0)
            previous_expenses_total = Decimal(0.0)

            current_expenses = Voucher.objects.filter(is_deleted=False, school_id = school_id, bank_account__account_type = accountType, financial_year__id = financialyear) or []
            for expense in current_expenses:
                amount = expense.totalAmount
                for votehead in votehead_list:
                    votehead_name = votehead.vote_head_name
                    if not expenses_votehead.get(votehead_name):
                        expenses_votehead[votehead_name]["name"] = votehead_name
                        expenses_votehead[votehead_name]["amount"] = Decimal(amount)
                        current_expenses_total += Decimal(amount)
                    else:
                        expenses_votehead[votehead_name]["amount"] += Decimal(amount)
                        current_expenses_total += Decimal(amount)

            if previous_year:
                previous_year_expenses = Voucher.objects.filter(is_deleted=False, account_type = accountType, school_id = school_id, financial_year = previous_year) or []
                for expense in previous_year_expenses:
                    amount = expense.totalAmount
                    for votehead in votehead_list:
                        votehead_name = votehead.vote_head_name
                        if not expenses_votehead.get(votehead_name):
                            expenses_votehead[votehead_name]["name"] = votehead_name
                            expenses_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                            previous_expenses_total += Decimal(amount)

                        else:
                            expenses_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                            previous_expenses_total += Decimal(amount)

                send = {
                    "account_type_name": accountype_name,
                    "current_expenses_total": current_expenses_total,
                    "previous_expenses_total": previous_expenses_total,
                    "expenses_votehead": expenses_votehead,
                }
                expenses_list.append(send)


        return Response({"detail": "save_object"})