import jdatetime
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Mission, Expense, Balance, Khodro

# فرم ثبت‌نام
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

# فرم ورود
class LoginForm(AuthenticationForm):
    pass

# فرم بودجه
class BudgetForm(forms.ModelForm):
    class Meta:
        model = Balance
        fields = ['amount']

# فرم ماموریت
class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['date', 'factory']
        mission_type = forms.ChoiceField(
        label='نوع مأموریت',
        choices=[
            ('normal', ' عادی'), 
            ('half', ' اصالت'), 
            ('holiday', ' تعطیل')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='normal'  # مقدار پیش‌فرض ماموریت عادی
    )

    date = forms.CharField(
        label='تاریخ',
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'placeholder': 'تاریخ شمسی نمونه 1403/10/10'
        }),
    )

    

    factory = forms.CharField(
        label='کارخانه',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کارخانه و محل ماموریت را وارد کنید'}),
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')

        # بررسی ماه و روز و تبدیل به دو رقمی اگر یک رقمی باشند
        date_parts = date.split('/')
        if len(date_parts) == 3:
            year, month, day = date_parts
            if len(month) == 1:  # اگر ماه تک رقمی است
                month = '0' + month  # اضافه کردن صفر به ماه
            if len(day) == 1:  # اگر روز تک رقمی است
                day = '0' + day  # اضافه کردن صفر به روز
            date = f"{year}/{month}/{day}"  # تاریخ اصلاح‌شده

        # اعتبارسنجی تاریخ شمسی
        try:
            jdatetime.datetime.strptime(date, '%Y/%m/%d')  # اعتبارسنجی تاریخ شمسی
        except ValueError:
            raise forms.ValidationError("فرمت تاریخ وارد شده صحیح نیست.")
        
        return date

    

    factory = forms.CharField(
        label='کارخانه',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کارخانه و محل ماموریت را وارد کنید'}),
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')

        # بررسی ماه و روز و تبدیل به دو رقمی اگر یک رقمی باشند
        date_parts = date.split('/')
        if len(date_parts) == 3:
            year, month, day = date_parts
            if len(month) == 1:  # اگر ماه تک رقمی است
                month = '0' + month  # اضافه کردن صفر به ماه
            if len(day) == 1:  # اگر روز تک رقمی است
                day = '0' + day  # اضافه کردن صفر به روز
            date = f"{year}/{month}/{day}"  # تاریخ اصلاح‌شده

        # اعتبارسنجی تاریخ شمسی
        try:
            jdatetime.datetime.strptime(date, '%Y/%m/%d')  # اعتبارسنجی تاریخ شمسی
        except ValueError:
            raise forms.ValidationError("فرمت تاریخ وارد شده صحیح نیست.")
        
        return date

# فرم هزینه
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'description', 'amount', 'factory']
    
    date = forms.CharField(
        label='تاریخ',
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'placeholder': 'تاریخ شمسی نمونه 1403/10/10'
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:  # فقط اگر فرم با داده پر نشده
            self.fields['date'].initial = jdatetime.datetime.now().strftime('%Y/%m/%d')

    amount = forms.CharField(
        label='مبلغ(ریال)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'لطفا مبلغ را وارد کنید'}),
    )

    description = forms.CharField(
        label='توضیحات',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'توضیحات'}),
    )

    factory = forms.CharField(
        label='کارخانه',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کارخانه و محل ماموریت را وارد کنید'}),
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')

        # بررسی ماه و روز و تبدیل به دو رقمی اگر یک رقمی باشند
        date_parts = date.split('/')
        if len(date_parts) == 3:
            year, month, day = date_parts
            if len(month) == 1:  # اگر ماه تک رقمی است
                month = '0' + month  # اضافه کردن صفر به ماه
            if len(day) == 1:  # اگر روز تک رقمی است
                day = '0' + day  # اضافه کردن صفر به روز
            date = f"{year}/{month}/{day}"  # تاریخ اصلاح‌شده
        
        # اعتبارسنجی تاریخ شمسی
        try:
            jdatetime.datetime.strptime(date, '%Y/%m/%d')  # اعتبارسنجی تاریخ شمسی
        except ValueError:
            raise forms.ValidationError("فرمت تاریخ وارد شده صحیح نیست.")
        
        return date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        try:
            amount = int(amount)
            if amount <= 0:
                raise forms.ValidationError("مبلغ باید بزرگ‌تر از صفر باشد.")
            return amount
        except (ValueError, TypeError):
            raise forms.ValidationError("لطفاً یک عدد صحیح وارد کنید.")

import jdatetime
from django import forms

# دریافت سال‌های شمسی
CURRENT_YEAR = jdatetime.date.today().year
YEAR_CHOICES = [(str(year), str(year)) for year in range(CURRENT_YEAR - 2, CURRENT_YEAR + 2)]  # سال‌های 10 سال اخیر شمسی

# انتخاب ماه و سال
MONTH_CHOICES = [
    ('', 'ماه را انتخاب کنید'),  # گزینه پیش‌فرض با مقدار خالی
    (1, 'فروردین'),
    (2, 'اردیبهشت'),
    (3, 'خرداد'),
    (4, 'تیر'),
    (5, 'مرداد'),
    (6, 'شهریور'),
    (7, 'مهر'),
    (8, 'آبان'),
    (9, 'آذر'),
    (10, 'دی'),
    (11, 'بهمن'),
    (12, 'اسفند'),
]

class ReportForm(forms.Form):
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label='ماه',
        initial='',  # مقدار پیش‌فرض را به گزینه خالی تنظیم می‌کند
        required=True,  # فیلد را اجباری می‌کند
        error_messages={
            'required': 'ماه را انتخاب کنید',  # پیام خطای سفارشی
        }
    )
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        label='سال',
        initial=str(CURRENT_YEAR),  # سال جاری پیش‌فرض
        required=True,  # فیلد را اجباری می‌کند
        error_messages={
            'required': 'سال را انتخاب کنید',  # پیام خطای سفارشی
        }
    )

# ویرایش نام کاربری ،پسورد ،نام ونام خانوادگی
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password']

    first_name = forms.CharField(
        label='نام',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_confirm = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password:
            if len(password) < 4:
                self.add_error('password', "رمز عبور باید حداقل ۴ کاراکتر باشد.")
            
            if password != password_confirm:
                self.add_error('password_confirm', "رمز عبور و تایید رمز عبور مطابقت ندارند.")
        else:
            if password_confirm:
                self.add_error('password', "رمز عبور الزامی است.")
                self.add_error('password_confirm', "لطفاً تایید رمز عبور را وارد کنید.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user
    #فرم هزینه خودرو
class KhodroForm(forms.ModelForm):
    class Meta:
        model = Khodro
        fields = ['date', 'kilometer' , 'amount', 'description']
    
    date = forms.CharField(
        label='تاریخ',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'تاریخ شمسی (مثال: 1403/10/10)',
            'id': 'datepicker'
        }),
    )
    amount = forms.CharField(
        label='مبلغ(ریال)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'لطفا مبلغ را وارد کنید', 'inputmode': 'numeric'}),
    )

    kilometer = forms.IntegerField(
        label='کیلومتر',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مقدار کیلومتر را وارد کنید'}),
    )
    description = forms.CharField(
        required=False,
        label='شرح سرویس',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'جزئیات سرویس را وارد کنید'}),
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        try:
            amount = int(amount)
            if amount <= 0:
                raise forms.ValidationError("مبلغ باید بزرگ‌تر از صفر باشد.")
            return amount
        except (ValueError, TypeError):
            raise forms.ValidationError("لطفاً یک عدد صحیح وارد کنید.")




