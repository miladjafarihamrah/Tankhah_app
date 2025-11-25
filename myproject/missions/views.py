from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .forms import SignUpForm, LoginForm
from .forms import MissionForm
from .forms import ExpenseForm
from .forms import KhodroForm
from .forms import ReportForm
from django.db.models import Sum



from .models import Mission
from .models import Expense  
from .models import Balance
from .models import Khodro
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
    total = Mission.objects.filter(
    user=request.user,
    date__startswith=f"{current_year}/{current_month:02d}"
    ).aggregate(Sum('mission_units'))['mission_units__sum'] or 0

    total_mission_units = int(total) if float(total).is_integer() else total


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
        'mission_count': total_mission_units,  # تعداد ماموریت‌های ماه جاری
        'balance': balance,  # ارسال مانده حساب به تمپلیت
    })

import os
from openpyxl import Workbook, load_workbook

def convert_persian_numbers_to_english(text):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_numbers = "۰۱۲۳۴۵۶۷۸۹"
    english_numbers = "0123456789"
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return text.translate(translation_table)

def add_mission(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = MissionForm(request.POST)
        if form.is_valid():
            mission = form.save(commit=False)
            mission.user = request.user

            # تبدیل اعداد فارسی به انگلیسی در تاریخ
            mission.date = convert_persian_numbers_to_english(mission.date)

            # مقدار تنظیم‌شده را اعمال کن
            mission_type_received = request.POST.get('mission_type', 'normal')
            mission.mission_type = mission_type_received
            mission.mission_units = {
                'normal': 1.0,
                'half': 0.5,
                'holiday': 2.0
            }.get(mission.mission_type, 1.0)  

            # بررسی تکراری نبودن تاریخ ماموریت برای همین کاربر
            existing_mission = Mission.objects.filter(user=request.user, date=mission.date).exists()
            if existing_mission:
                messages.error(request, 'خطا: تاریخ ماموریت تکراری است.')
                return render(request, 'add_mission.html', {'form': form})

            mission.save()
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

            # تبدیل اعداد فارسی به انگلیسی در تاریخ
            expense.date = convert_persian_numbers_to_english(expense.date)
            
            # تبدیل مبلغ به عدد صحیح
            try:
                expense.amount = int(expense.amount)
            except ValueError:
                messages.error(request, 'مبلغ وارد شده معتبر نیست.')
                return render(request, 'add_expense.html', {'form': form})

            # کاهش مانده حساب
            try:
                balance = Balance.objects.get(user=request.user)
                balance.amount -= expense.amount
                balance.save()
            except Balance.DoesNotExist:
                messages.error(request, 'خطا: حسابی برای این کاربر ثبت نشده است.')
                return render(request, 'add_expense.html', {'form': form})

            expense.save()
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
                if year < 1400 or year > 1450:
                    messages.error(request, 'سال وارد شده نامعتبر است.')
                    return redirect('home')

            except (ValueError, KeyError):
                messages.error(request, 'خطا در پردازش داده‌ها.')
                return redirect('home')

            # دریافت نوع گزارش
            report_type = request.POST.get('report_type')
            REPORT_TYPES = ('mission', 'expense', 'khodro', 'mission_pdf', 'expense_pdf', 'khodro_pdf')

            # بررسی معتبر بودن نوع گزارش
            if report_type not in REPORT_TYPES:
                messages.error(request, 'نوع گزارش نامعتبر است.')
                return redirect('home')

            # اگر نوع گزارش PDF است، به تابع مربوطه هدایت کنیم
            if report_type.endswith('_pdf'):
                return generate_pdf_report(request)

            # تعیین نوع مدل
            model_type = report_type

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
                    'header': ['ردیف', 'تاریخ', 'توضیحات', 'مبلغ(ریال)', 'کارخانه']
                },
                'khodro': {
                    'model': Khodro,
                    'output_name': f"k_{request.user.username}_{year}_{month}.xlsx",
                    'header': ['ردیف', 'تاریخ', 'کیلومتر', 'شرح سرویس', 'مبلغ(ریال)']
                }
            }

            config = report_config[model_type]
            model = config['model']
            output_name = config['output_name']
            header = config['header']

            # دریافت داده‌ها از دیتابیس
            data = model.objects.filter(user=request.user)
            filtered_data = []
            total_amount = 0  # جمع کل مبالغ

            if model_type == 'mission':
                # جدا کردن ماموریت‌های عادی و تعطیل
                normal_missions = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year and item.mission_type != 'half':
                        normal_missions.append({
                            'factory': item.factory,
                            'date': item.date,
                            'type': item.mission_type
                        })

                # مرتب‌سازی ماموریت‌های عادی و تعطیل بر اساس تاریخ
                normal_missions.sort(key=lambda x: x['date'])

                # اضافه کردن ماموریت‌های عادی و تعطیل به جدول
                for mission in normal_missions:
                    filtered_data.append([mission['factory'], convert_to_persian_numbers(mission['date'])])
                    if mission['type'] == 'holiday':
                        filtered_data.append([f"{mission['factory']} (تعطیل)", convert_to_persian_numbers(mission['date'])])

                # جدا کردن و مرتب‌سازی ماموریت‌های اصالت
                asalat_missions = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year and item.mission_type == 'half':
                        asalat_missions.append({
                            'factory': item.factory,
                            'date': item.date
                        })

                # مرتب‌سازی ماموریت‌های اصالت بر اساس تاریخ
                asalat_missions.sort(key=lambda x: x['date'])

                # اضافه کردن عنوان اصالت فقط اگر ماموریت اصالت وجود داشته باشد
                if asalat_missions:
                    filtered_data.append(["", "اصالت"])

                # اضافه کردن ماموریت‌های اصالت به جدول
                asalat_count = 1
                for mission in asalat_missions:
                    filtered_data.append([mission['factory'], convert_to_persian_numbers(mission['date'])])
                    asalat_count += 1
            else:
                # برای گزارش‌های تنخواه و خودرو
                temp_data = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year:
                        if model_type == 'expense':
                            temp_data.append({
                                'date': item.date,
                                'factory': item.factory,
                                'description': item.description,
                                'amount': item.amount
                            })
                            total_amount += item.amount
                        elif model_type == 'khodro':
                            temp_data.append({
                                'date': item.date,
                                'amount': item.amount,
                                'description': item.description,
                                'kilometer': item.kilometer
                            })
                            total_amount += item.amount

                # مرتب‌سازی بر اساس تاریخ
                temp_data.sort(key=lambda x: x['date'])

                # اضافه کردن داده‌های مرتب شده به filtered_data
                for index, item in enumerate(temp_data, 1):
                    if model_type == 'expense':
                        filtered_data.append([
                            item['factory'],
                            convert_to_persian_numbers(item['amount']),
                            item['description'],
                            convert_to_persian_numbers(item['date'])
                        ])
                    elif model_type == 'khodro':
                        filtered_data.append([
                            convert_to_persian_numbers(item['amount']),
                            item['description'],
                            convert_to_persian_numbers(item['kilometer']),
                            convert_to_persian_numbers(item['date'])
                        ])

            # ایجاد فایل اکسل
            wb = Workbook()
            ws = wb.active
            ws.sheet_view.rightToLeft = True
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

            # اضافه کردن داده‌ها به فایل اکسل
            for index, row in enumerate(filtered_data, 1):
                rtl_row = []
                for item in row:
                    if item == "اصالت":
                        # استایل مخصوص برای سطر اصالت
                        asalat_style = ParagraphStyle(
                            'AsalatStyle',
                            parent=styles['RTL'],
                            fontSize=14,
                            textColor=colors.darkblue,
                            fontName='Vazir'
                        )
                        rtl_row.append(Paragraph(get_display(reshape(str(item))), asalat_style))
                    else:
                        rtl_row.append(Paragraph(get_display(reshape(str(item))), styles['RTL']))
                # اضافه کردن شماره ردیف
                rtl_row.append(Paragraph(get_display(reshape(str(index))), styles['RTL']))
                table_data.append(rtl_row)

            # اضافه کردن سطر جمع کل به جدول
            if model_type in ['expense', 'khodro'] and filtered_data:
                if model_type == 'expense':
                    ws.append(['', '', 'جمع کل(ریال)', total_amount, ''])
                else:  # khodro
                    ws.append(['', '', '', 'جمع کل(ریال):', f"{total_amount:,}"])

            # اعمال استایل به داده‌ها
            data_font = Font(size=14, name="B Nazanin")  # سایز فونت ۱۴
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(header)):
                for cell in row:
                    cell.font = data_font
                    cell.border = border
                    cell.alignment = alignment

            # فرمت سه رقم سه رقم جدا کردن اعداد
            if report_type in ['expense', 'khodro']:
                amount_column = 4 if report_type == 'expense' else 5
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=amount_column, max_col=amount_column):
                    for cell in row:
                        if isinstance(cell.value, (int, float)):
                            cell.number_format = '#,##0'

            # اضافه کردن جای امضا
            ws.append([])  # سطر خالی
            ws.append([])
            ws.append([])
            if report_type == "expense":
                ws.append(["", request.user.first_name, "کنترل کننده", "مدیر عامل"])
                ws.append(["", request.user.last_name])
            else:
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

def hazineh_khodro(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = KhodroForm(request.POST)
        if form.is_valid():
            khodro = form.save(commit=False)
            khodro.user = request.user

            # تبدیل اعداد فارسی به انگلیسی در تاریخ
            khodro.date = convert_persian_numbers_to_english(khodro.date)
            
            # تبدیل مبلغ به عدد صحیح
            try:
                khodro.amount = int(khodro.amount)
            except ValueError:
                messages.error(request, 'مبلغ وارد شده معتبر نیست.')
                return render(request, 'hazineh_khodro.html', {'form': form})

            # کاهش مانده حساب
            balance = Balance.objects.get(user=request.user)
            balance.amount -= khodro.amount
            balance.save()

            khodro.save()
            return redirect('home')
        else:
            messages.error(request, 'خطا در ثبت تنخواه. لطفاً دوباره تلاش کنید.')
    else:
        form = KhodroForm()
    return render(request, 'hazineh_khodro.html', {'form': form})
# ویرایش هزینه‌ها
def edit_khodro(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    
    if not year or not month :
        return render(request, 'error.html', {'message': 'سال وماه  معتبر نیست.'})

    # فیلتر کردن هزینه‌ها بر اساس ماه
    khodros = Khodro.objects.filter(user=request.user)
    khodros = [khodro for khodro in khodros 
               if khodro.date.split('/')[0] == year
               and khodro.date.split('/')[1] == month]

    return render(request, 'edit_khodro.html', {
        'khodros': khodros,
        'month': month,
        'year': year,
          })


def delete_khodro(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'احراز هویت لازم است.'})
    
    khodro_id = request.GET.get('id')  # دریافت id به جای date

    if not khodro_id:
        return JsonResponse({'status': 'error', 'message': 'شناسه نامعتبر است.'})

    # حذف khodro بر اساس ID
    khodro = get_object_or_404(Khodro, id=khodro_id, user=request.user)
    amount = khodro.amount  # مقدار هزینه برای به‌روزرسانی مانده حساب
    khodro.delete()

    # افزایش مانده حساب
    balance = Balance.objects.get(user=request.user)
    balance.amount += amount
    balance.save()

    return JsonResponse({'status': 'success', 'message': 'هزینه خودرو با موفقیت حذف شد.'})

def edit_khodro_details(request):
    khodro_id = request.GET.get('id')
    kilometer = request.GET.get('kilometer')
    amount = request.GET.get('amount')
    description = request.GET.get('description')

    print(f"Khodro ID: {khodro_id}")  # برای دیباگ

    # بررسی اینکه مبلغ به عدد تبدیل شود
    try:
        amount = float(amount)  # تبدیل مبلغ به نوع عددی (float)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'مقدار مبلغ معتبر نیست.'})

    try:
        # پیدا کردن رکورد مطابق با ID
        khodro = Khodro.objects.get(id=khodro_id)

        # ذخیره مبلغ قدیمی برای به‌روزرسانی مانده حساب
        old_amount = khodro.amount

        # به‌روزرسانی اطلاعات هزینه
        khodro.kilometer = kilometer
        khodro.amount = amount
        khodro.description = description
        khodro.save()  # ذخیره تغییرات در پایگاه داده

        # به‌روزرسانی مانده حساب
        balance = Balance.objects.get(user=request.user)
        
        # کم کردن مبلغ قدیمی و اضافه کردن مبلغ جدید
        balance.amount += (old_amount - amount)
        balance.save()

        return JsonResponse({'status': 'success'})
    except Khodro.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'تنخواه پیدا نشد!'})
    except Balance.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'موجودی کاربر یافت نشد!'})
MISSION_TYPE_DISPLAY = {
    'normal': '',
    'half': 'اصالت',
    'holiday': 'تعطیل'
}

# در ویو یا تمپلیت:
mission_type_display = MISSION_TYPE_DISPLAY.get(Mission.mission_type,'')

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from django.conf import settings

# تنظیم مسیر فونت
FONT_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Vazir.ttf')

def generate_pdf_report(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            try:
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])
                
                if not (1 <= month <= 12):
                    messages.error(request, 'ماه وارد شده نامعتبر است.')
                    return redirect('home')
                
                if year < 1400 or year > 1450:
                    messages.error(request, 'سال وارد شده نامعتبر است.')
                    return redirect('home')

            except (ValueError, KeyError):
                messages.error(request, 'خطا در پردازش داده‌ها.')
                return redirect('home')

            report_type = request.POST.get('report_type')
            REPORT_TYPES = ('mission_pdf', 'expense_pdf', 'khodro_pdf')

            if report_type not in REPORT_TYPES:
                messages.error(request, 'نوع گزارش نامعتبر است.')
                return redirect('home')

            model_type = report_type.replace('_pdf', '')
            
            report_config = {
                'mission': {
                    'model': Mission,
                    'output_name': f"m_{request.user.username}_{year}_{month}.pdf",
                    'title': 'گزارش ماموریت‌ها',
                    'headers': ['کارخانه', 'تاریخ', 'ردیف']  # ترتیب از راست به چپ
                },
                'expense': {
                    'model': Expense,
                    'output_name': f"t_{request.user.username}_{year}_{month}.pdf",
                    'title': 'گزارش تنخواه‌ها',
                    'headers': ['کارخانه', 'مبلغ(ریال)', 'توضیحات', 'تاریخ', 'ردیف']  # ترتیب از راست به چپ
                },
                'khodro': {
                    'model': Khodro,
                    'output_name': f"k_{request.user.username}_{year}_{month}.pdf",
                    'title': 'گزارش هزینه‌های خودرو',
                    'headers': ['مبلغ(ریال)', 'شرح سرویس', 'کیلومتر', 'تاریخ', 'ردیف']  # ترتیب از راست به چپ
                }
            }

            config = report_config[model_type]
            model = config['model']
            output_name = config['output_name']
            title = config['title']
            headers = config['headers']

            # دریافت داده‌ها
            data = model.objects.filter(user=request.user)
            filtered_data = []
            total_amount = 0

            if model_type == 'mission':
                # جدا کردن ماموریت‌های عادی و تعطیل
                normal_missions = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year and item.mission_type != 'half':
                        normal_missions.append({
                            'factory': item.factory,
                            'date': item.date,
                            'type': item.mission_type
                        })

                # مرتب‌سازی ماموریت‌های عادی و تعطیل بر اساس تاریخ
                normal_missions.sort(key=lambda x: x['date'])

                # اضافه کردن ماموریت‌های عادی و تعطیل به جدول
                for mission in normal_missions:
                    filtered_data.append([mission['factory'], convert_to_persian_numbers(mission['date'])])
                    if mission['type'] == 'holiday':
                        filtered_data.append([f"{mission['factory']} (تعطیل)", convert_to_persian_numbers(mission['date'])])

                # جدا کردن و مرتب‌سازی ماموریت‌های اصالت
                asalat_missions = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year and item.mission_type == 'half':
                        asalat_missions.append({
                            'factory': item.factory,
                            'date': item.date
                        })

                # مرتب‌سازی ماموریت‌های اصالت بر اساس تاریخ
                asalat_missions.sort(key=lambda x: x['date'])

                # اضافه کردن عنوان اصالت فقط اگر ماموریت اصالت وجود داشته باشد
                if asalat_missions:
                    filtered_data.append(["", "اصالت"])

                # اضافه کردن ماموریت‌های اصالت به جدول
                asalat_count = 1
                for mission in asalat_missions:
                    filtered_data.append([mission['factory'], convert_to_persian_numbers(mission['date'])])
                    asalat_count += 1
            else:
                # برای گزارش‌های تنخواه و خودرو
                temp_data = []
                for item in data:
                    item_date = item.date
                    item_year, item_month, item_day = map(int, item_date.split('/'))
                    if item_month == month and item_year == year:
                        if model_type == 'expense':
                            temp_data.append({
                                'date': item.date,
                                'factory': item.factory,
                                'description': item.description,
                                'amount': item.amount
                            })
                            total_amount += item.amount
                        elif model_type == 'khodro':
                            temp_data.append({
                                'date': item.date,
                                'amount': item.amount,
                                'description': item.description,
                                'kilometer': item.kilometer
                            })
                            total_amount += item.amount

                # مرتب‌سازی بر اساس تاریخ
                temp_data.sort(key=lambda x: x['date'])

                # اضافه کردن داده‌های مرتب شده به filtered_data
                for index, item in enumerate(temp_data, 1):
                    if model_type == 'expense':
                        filtered_data.append([
                            item['factory'],
                            convert_to_persian_numbers(item['amount']),
                            item['description'],
                            convert_to_persian_numbers(item['date'])
                        ])
                    elif model_type == 'khodro':
                        filtered_data.append([
                            convert_to_persian_numbers(item['amount']),
                            item['description'],
                            convert_to_persian_numbers(item['kilometer']),
                            convert_to_persian_numbers(item['date'])
                        ])

            # ایجاد پاسخ HTTP
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{output_name}"'

            # ایجاد PDF با استفاده از SimpleDocTemplate
            doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            
            # ثبت فونت
            pdfmetrics.registerFont(TTFont('Vazir', FONT_PATH))

            # تعریف استایل‌ها
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='RTL',
                                    fontName='Vazir',
                                    fontSize=8,
                                    alignment=1,  # وسط چین
                                    textColor=colors.black,
                                    leading=6))  # فاصله بین خطوط

            # آماده‌سازی داده‌ها برای جدول
            table_data = []
            
            # تبدیل عنوان‌ها به راست به چپ
            rtl_headers = [Paragraph(get_display(reshape(header)), styles['RTL']) for header in headers]
            table_data.append(rtl_headers)

            # تبدیل داده‌ها به راست به چپ
            for index, row in enumerate(filtered_data, 1):
                rtl_row = []
                for item in row:
                    if item == "اصالت":
                        # استایل مخصوص برای سطر اصالت
                        asalat_style = ParagraphStyle(
                            'AsalatStyle',
                            parent=styles['RTL'],
                            fontSize=14,
                            textColor=colors.darkblue,
                            fontName='Vazir'
                        )
                        rtl_row.append(Paragraph(get_display(reshape(str(item))), asalat_style))
                    else:
                        rtl_row.append(Paragraph(get_display(reshape(str(item))), styles['RTL']))
                # اضافه کردن شماره ردیف
                rtl_row.append(Paragraph(get_display(reshape(str(index))), styles['RTL']))
                table_data.append(rtl_row)

            # ایجاد جدول
            # تنظیم عرض ستون‌ها بر اساس نوع گزارش
            if model_type == 'mission':
                col_widths = [150, 90, 40]  # [کارخانه، تاریخ، ردیف]
            elif model_type == 'expense':
                col_widths = [90, 90, 180, 90, 40]  # [کارخانه، مبلغ، توضیحات، تاریخ، ردیف]
            elif model_type == 'khodro':
                col_widths = [90, 180, 70, 90, 40]  # [مبلغ، شرح سرویس، کیلومتر، تاریخ، ردیف]

            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # استایل جدول
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Vazir'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),  # سایز فونت هدر
                ('FONTSIZE', (0, 1), (-1, -1), 11),  # سایز فونت داده‌ها
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('ALIGN', (-2, 1), (-2, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
            ]))

            # اضافه کردن استایل برای سطر اصالت
            for i, row in enumerate(table_data):
                if isinstance(row[0], Paragraph) and row[0].text == "اصالت":
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightgrey),
                        ('FONT', (0, i), (-1, i), 'Vazir'),
                        ('FONTSIZE', (0, i), (-1, i), 14),
                        ('TEXTCOLOR', (0, i), (-1, i), colors.darkblue),
                    ]))
                    break

            # لیست المان‌های PDF
            elements = []

            # اضافه کردن عنوان
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['RTL'],
                fontSize=16,
                spaceAfter=30  # فاصله بعد از عنوان
            )
            title_text = get_display(reshape(f"{title} - {year}/{month:02d}"))
            elements.append(Paragraph(title_text, title_style))

            # اضافه کردن جدول
            elements.append(table)

            # اضافه کردن جمع کل برای گزارش‌های مالی
            if model_type in ['expense', 'khodro'] and filtered_data:
                total_style = ParagraphStyle(
                    'Total',
                    parent=styles['RTL'],
                    fontSize=10,
                    spaceBefore=20
                )
                total_text = get_display(reshape(f"جمع کل: {convert_to_persian_numbers(total_amount)} ریال"))
                elements.append(Paragraph(total_text, total_style))

            # اضافه کردن یک خط خالی برای فاصله بیشتر
            elements.append(Paragraph("<br/><br/><br/>", styles['RTL']))

            # اضافه کردن محل‌های امضا با استفاده از جدول
            signature_style = ParagraphStyle(
                'Signature',
                parent=styles['RTL'],
                fontSize=12,
                spaceBefore=150  # فاصله قبل از امضاها
            )

            # ایجاد جدول برای امضاها
            signature_table_data = [[
                Paragraph(get_display(reshape("مدیر عامل")), signature_style),
                Paragraph(get_display(reshape("کنترل کننده")), signature_style),
                Paragraph(get_display(reshape(f"{request.user.get_full_name()}")), signature_style)
            ]]
            
            signature_table = Table(signature_table_data, colWidths=[180, 180, 180])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),    # مدیر عامل - چپ چین
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # کنترل کننده - وسط چین
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),   # نام کاربر - راست چین
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            elements.append(signature_table)

            # ساخت PDF
            doc.build(elements)
            return response
        
    else:
        form = ReportForm()
    return render(request, 'report.html', {'form': form})

def convert_to_persian_numbers(text):
    """تبدیل اعداد انگلیسی به فارسی و اضافه کردن جداکننده سه رقمی"""
    english_numbers = "0123456789"
    persian_numbers = "۰۱۲۳۴۵۶۷۸۹"
    translation_table = str.maketrans(english_numbers, persian_numbers)
    
    # تبدیل به رشته و اضافه کردن جداکننده سه رقمی
    text = str(text)
    if text.isdigit():
        text = "{:,}".format(int(text))
    
    # تبدیل اعداد به فارسی
    return text.translate(translation_table)

