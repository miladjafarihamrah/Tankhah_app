from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .forms import SignUpForm, LoginForm
from .forms import MissionForm
from .forms import ExpenseForm
from .forms import ReportForm


from .models import Mission
from .models import Expense  
from .models import Balance
from .models import TransactionHistory


import jdatetime
from django.http import JsonResponse
import os
from datetime import datetime
from openpyxl import load_workbook, Workbook
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm
# دیکشنری برای تبدیل نام ماه‌های شمسی به انگلیسی
PERSIAN_MONTH_TO_ENGLISH = {
    'فروردین': 'Farvardin',
    'اردیبهشت': 'Ordibehesht',
    'خرداد': 'Khordad',
    'تیر': 'Tir',
    'مرداد': 'Mordad',
    'شهریور': 'Shahrivar',
    'مهر': 'Mehr',
    'آبان': 'Aban',
    'آذر': 'Azar',
    'دی': 'Dey',
    'بهمن': 'Bahman',
    'اسفند': 'Esfand'
}


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})
#ویرایش نام کاربری ،پسورود ،نام ونام خانوادگی
@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات شما با موفقیت به‌روزرسانی شد.")
            return redirect('home')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'update_profile.html', {'form': form})
#صفحه اصلی برنامه
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # دریافت تاریخ جاری به صورت شمسی
    today = jdatetime.datetime.now().strftime('%Y/%m/%d')
    
    # دریافت تاریخ جاری شمسی
    current_jalali = jdatetime.datetime.now()
    current_year = current_jalali.year
    current_month = current_jalali.month

# فیلتر ماموریت‌های ماه و سال جاری
    mission_count = Mission.objects.filter(
    user=request.user,
    date__startswith=f"{current_year}/{current_month:02d}"
     ).count()

    full_name = f"{request.user.first_name} {request.user.last_name}"
                
    # دریافت مانده حساب
    try:
        balance = Balance.objects.get(user=request.user).amount
    except Balance.DoesNotExist:
        # اگر مانده حساب وجود نداشت، یک مانده حساب جدید ایجاد کنید
        balance = 4000000  # مقدار پیش‌فرض
        Balance.objects.create(user=request.user, amount=balance)

    return render(request, 'home.html', {
        'full_name': full_name,
        'today': today,
        'mission_count': mission_count,  # تعداد ماموریت‌های ماه جاری
        'balance': balance,  # ارسال مانده حساب به تمپلیت
    })

import os
from openpyxl import Workbook, load_workbook

def add_mission(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = MissionForm(request.POST)
        if form.is_valid():
            mission = form.save(commit=False)
            mission.user = request.user

            # بررسی تکراری نبودن تاریخ ماموریت
            existing_mission = Mission.objects.filter(user=request.user, date=mission.date).exists()
            if existing_mission:
                messages.error(request, 'خطا: تاریخ ماموریت تکراری است.')
                return render(request, 'add_mission.html', {'form': form})

            mission.save()  # ذخیره در دیتابیس
            return redirect('home')
        else:
            messages.error(request, 'خطا در ثبت ماموریت. لطفاً دوباره تلاش کنید.')
    else:
        form = MissionForm()
    return render(request, 'add_mission.html', {'form': form})
def edit_mission(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not year or not month:
        return render(request, 'error.html', {'message': 'سال و ماه معتبر نیست.'})

    # فیلتر کردن ماموریت‌ها بر اساس سال و ماه
    missions = Mission.objects.filter(user=request.user)
    missions = [mission for mission in missions 
               if mission.date.split('/')[0] == year 
               and mission.date.split('/')[1] == month]

    return render(request, 'edit_mission.html', {
        'missions': missions, 
        'month': month,
        'year': year
    })

def delete_mission(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'احراز هویت لازم است.'})
    
    date = request.GET.get('date')  # دریافت تاریخ از درخواست GET
    if not date:
        return JsonResponse({'status': 'error', 'message': 'تاریخ نامعتبر است.'})

    # حذف ماموریت از دیتابیس
    mission = get_object_or_404(Mission, date=date, user=request.user)
    mission.delete()

    return JsonResponse({'status': 'success', 'message': 'ماموریت با موفقیت حذف شد.'})


  


def add_expense(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

            # کاهش مانده حساب
            balance = Balance.objects.get(user=request.user)
            balance.amount -= expense.amount
            balance.save()

        
            return redirect('home')
        else:
            messages.error(request, 'خطا در ثبت تنخواه. لطفاً دوباره تلاش کنید.')
    else:
        form = ExpenseForm()
    return render(request, 'add_expense.html', {'form': form})

# ویرایش هزینه‌ها
def edit_expense(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not year or not month:
        return render(request, 'error.html', {'message': 'سال و ماه معتبر نیست.'})

    # فیلتر کردن هزینه‌ها بر اساس ماه
    expenses = Expense.objects.filter(user=request.user)
    expenses = [expense for expense in expenses 
               if expense.date.split('/')[0] == year 
               and expense.date.split('/')[1] == month]

    return render(request, 'edit_expense.html', {
        'expenses': expenses,
        'month': month,
        'year': year
          })



def delete_expense(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'احراز هویت لازم است.'})
    
    expense_id = request.GET.get('id')  # دریافت id به جای date

    if not expense_id:
        return JsonResponse({'status': 'error', 'message': 'شناسه نامعتبر است.'})

    # حذف Expense بر اساس ID
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    amount = expense.amount  # مقدار هزینه برای به‌روزرسانی مانده حساب
    expense.delete()

    # افزایش مانده حساب
    balance = Balance.objects.get(user=request.user)
    balance.amount += amount
    balance.save()

    return JsonResponse({'status': 'success', 'message': 'تنخواه با موفقیت حذف شد.'})

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from datetime import datetime
from .forms import ReportForm
from .models import Mission, Expense
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.workbook import Workbook
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime

def generate_report(request):
    # بررسی احراز هویت کاربر
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            try:
                # دریافت و اعتبارسنجی ماه و سال
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])
                
                if not (1 <= month <= 12):
                    messages.error(request, 'ماه وارد شده نامعتبر است.')
                    return redirect('home')
                
                # اطمینان از معتبر بودن سال
                if year < 1400 or year > 1450:  # یا هر شرط مناسب دیگری برای سال
                    messages.error(request, 'سال وارد شده نامعتبر است.')
                    return redirect('home')

            except (ValueError, KeyError):
                messages.error(request, 'خطا در پردازش داده‌ها.')
                return redirect('home')

            # دریافت نوع گزارش
            report_type = request.POST.get('report_type')
            REPORT_TYPES = ('mission', 'expense',)

            # بررسی معتبر بودن نوع گزارش
            if report_type not in REPORT_TYPES:
                messages.error(request, 'نوع گزارش نامعتبر است.')
                return redirect('home')

            # تنظیمات مربوط به نوع گزارش
            report_config = {
                'mission': {
                    'model': Mission,
                    'output_name': f"m_{request.user.username}_{year}_{month}.xlsx",
                    'header': ['ردیف', 'تاریخ', 'کارخانه']
                },
                'expense': {
                    'model': Expense,
                    'output_name': f"t_{request.user.username}_{year}_{month}.xlsx",
                    'header': ['ردیف', 'تاریخ', 'توضیحات', 'مبلغ', 'کارخانه']
                }
            }

            config = report_config[report_type]
            model = config['model']
            output_name = config['output_name']
            header = config['header']

            # دریافت داده‌ها از دیتابیس
            data = model.objects.filter(user=request.user)
            filtered_data = []
            total_amount = 0  # جمع کل مبالغ

            for item in data:
                item_date = item.date  # تاریخ به صورت رشته (مثلاً '1402/07/15')
                item_year, item_month, _ = map(int, item_date.split('/'))  # استخراج سال و ماه از تاریخ
                
                # فیلتر کردن داده‌ها بر اساس ماه و سال
                if item_month == month and item_year == year:
                    # تبدیل تاریخ به فرمت datetime برای مرتب‌سازی
                    date_obj = datetime.strptime(item_date, '%Y/%m/%d')
                    
                    if report_type == 'mission':
                        filtered_data.append([date_obj, item.date, item.factory])
                    elif report_type == 'expense':
                        # محاسبه جمع کل مبالغ
                        total_amount += item.amount
                        filtered_data.append([date_obj, item.date, item.description, item.amount, item.factory])

            # مرتب‌سازی داده‌ها بر اساس تاریخ (صعودی)
            filtered_data.sort(key=lambda x: x[0])  # x[0] همان date_obj است

            # حذف date_obj از داده‌ها (چون فقط برای مرتب‌سازی استفاده شد)
            filtered_data = [item[1:] for item in filtered_data]

            # ایجاد فایل اکسل جدید
            wb = Workbook()
            ws = wb.active
            ws.sheet_view.rightToLeft = True  # تنظیم جهت صفحه به راست‌چین
            ws.append(header)

            # تنظیم فونت کلی اکسل به "B Nazanin"
            default_font = Font(name="B Nazanin", size=14)
            
            # تنظیم استایل برای هدرها
            header_font = Font(bold=True, color="FFFFFF", size=14, name="B Nazanin")  # فونت پررنگ، رنگ سفید و سایز ۱۴
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")  # رنگ پس‌زمینه آبی
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )  # حاشیه نازک برای سلول‌ها
            alignment = Alignment(horizontal='center', vertical='center')  # تراز وسط

            # اعمال استایل به هدرها
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = alignment

            # اضافه کردن داده‌ها به فایل اکسل همراه با شماره ردیف
            for index, row in enumerate(filtered_data, start=1):
                ws.append([index] + row)  # اضافه کردن شماره ردیف به ابتدای سطر

            # اعمال استایل به داده‌ها (سایز فونت ۱۴ برای تمام سلول‌ها)
            data_font = Font(size=14, name="B Nazanin")  # سایز فونت ۱۴
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(header)):
                for cell in row:
                    cell.font = data_font
                    cell.border = border
                    cell.alignment = alignment

            # فرمت سه رقم سه رقم جدا کردن اعداد برای ستون مبلغ و جمع کل
            if report_type == 'expense':
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=4, max_col=4):  # ستون مبلغ
                    for cell in row:
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = '#,##0'  # جدا کردن سه رقم سه رقم

                if filtered_data:
                    # اضافه کردن سطر جمع کل
                    ws.append(['', '', 'جمع کل(تومان)', total_amount, ''])
                    # اعمال استایل به سطر جمع کل
                    for cell in ws[ws.max_row]:
                        cell.font = Font(size=14, bold=True, name="B Nazanin")  # فونت بولد و سایز ۱۴
                        cell.border = border
                        cell.alignment = alignment
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = '#,##0'  # جدا کردن سه رقم سه رقم

            # اضافه کردن جای امضا در پایین صفحه
            ws.append([])  # یک سطر خالی
            ws.append([])  # یک سطر خالی
            ws.append([])  # یک سطر خالی
            if report_type == "expense":  # اگر گزارش از نوع "تنخواه" است
             ws.append(["", request.user.first_name, "کنترل کننده", "مدیر عامل"])  # ستون اول خالی
             ws.append(["", request.user.last_name])  # ستون اول خالی برای نام خانوادگی
            else:  # برای سایر گزارش‌ها (مثلاً "ماموریت")
             ws.append([request.user.first_name, "کنترل کننده", "مدیر عامل"])
             ws.append([request.user.last_name])

            # تنظیم خودکار اندازه ستون‌ها
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter  # نام ستون (مثلاً A, B, C)
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 4) * 1.2  # محاسبه عرض ستون
                ws.column_dimensions[column].width = adjusted_width

            # تنظیمات صفحه برای پرینت
            ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT  # جهت صفحه به صورت عمودی
            ws.page_setup.paperSize = ws.PAPERSIZE_A4  # اندازه کاغذ A4
            ws.page_setup.fitToWidth = 1  # تنظیم عرض صفحه برای پرینت
            ws.page_setup.fitToHeight = 0  # عدم تنظیم ارتفاع صفحه
            ws.page_setup.horizontalCentered = True  # فعال کردن گزینه Horizontally در حاشیه‌ها

            # تنظیم حاشیه‌ها
            ws.page_margins.left = 0.5
            ws.page_margins.right = 0.5
            ws.page_margins.top = 0.5
            ws.page_margins.bottom = 0.5
            ws.page_margins.header = 0.3
            ws.page_margins.footer = 0.3

         # تنظیم هدر و فوتر
            ws.oddHeader.center.text = "گزارش ماهانه ماموریت" if report_type == "mission" else "گزارش ماهانه تنخواه"
            ws.oddFooter.center.text = "صفحه &P از &N"  # فوتر وسط صفحه (شماره صفحه)
            # تنظیم هدرهای HTTP برای دانلود فایل
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{output_name}"'

            # ذخیره فایل در پاسخ
            wb.save(response)
            return response
        
    else:
        form = ReportForm()
    return render(request, 'report.html', {'form': form})

def update_balance(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0))
        action = request.POST.get('action')  # 'increase' یا 'decrease'

        if amount <= 0:
            messages.error(request, 'مبلغ وارد شده نامعتبر است.')
            return redirect('home')

        balance = Balance.objects.get(user=request.user)
        if action == 'increase':
            balance.amount += amount
        elif action == 'decrease':
            balance.amount -= amount
        balance.save()

        # ذخیره در تاریخچه
        TransactionHistory.objects.create(
            user=request.user,
            amount=amount if action == 'increase' else -amount,  # مثبت/منفی
            action=action
        )

        messages.success(request, f'مانده حساب با موفقیت {"افزایش" if action == "increase" else "کاهش"} یافت.')
        return redirect('home')
    else:
        return redirect('home')
    

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Mission  # مطمئن شو مدل درست ایمپورت شده

@csrf_exempt
def update_mission_factory(request, mission_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            factory_name = data.get('factory')

            mission = Mission.objects.get(id=mission_id)
            mission.factory = factory_name
            mission.save()

            return JsonResponse({'status': 'success'})
        except Mission.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'مأموریت پیدا نشد'})
    return JsonResponse({'status': 'error', 'message': 'درخواست نامعتبر'})

# views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import Expense, Balance  # فرض بر این است که مدل Expense و Balance موجود است

def edit_expense_details(request):
    expense_id = request.GET.get('id')
    factory = request.GET.get('factory')
    amount = request.GET.get('amount')
    description = request.GET.get('description')

    print(f"Expense ID: {expense_id}")  # برای دیباگ

    # بررسی اینکه مبلغ به عدد تبدیل شود
    try:
        amount = float(amount)  # تبدیل مبلغ به نوع عددی (float)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'مقدار مبلغ معتبر نیست.'})

    try:
        # پیدا کردن رکورد مطابق با ID
        expense = Expense.objects.get(id=expense_id)

        # ذخیره مبلغ قدیمی برای به‌روزرسانی مانده حساب
        old_amount = expense.amount

        # به‌روزرسانی اطلاعات هزینه
        expense.factory = factory
        expense.amount = amount
        expense.description = description
        expense.save()  # ذخیره تغییرات در پایگاه داده

        # به‌روزرسانی مانده حساب
        balance = Balance.objects.get(user=request.user)
        
        # کم کردن مبلغ قدیمی و اضافه کردن مبلغ جدید
        balance.amount += (old_amount - amount)
        balance.save()

        return JsonResponse({'status': 'success'})
    except Expense.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'تنخواه پیدا نشد!'})
    except Balance.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'موجودی کاربر یافت نشد!'})

