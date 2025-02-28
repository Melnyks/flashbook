from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from homepage.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.utils import IntegrityError
# Create your views here.

def homepage(request):
    return render(request, 'homepage.html')

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            try:
                # สร้าง User ใหม่
                newUser = User.objects.create(
                    user=form.cleaned_data['username'],
                    fname=form.cleaned_data['fname'],
                    lname=form.cleaned_data['lname'],
                    email=form.cleaned_data['email'],
                )
                newUser.set_password(form.cleaned_data['password1'])
                newUser.save()

                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
            except IntegrityError as e:
                # ตรวจสอบว่า error เกี่ยวกับ email ซ้ำหรือไม่
                if 'unique constraint' in str(e).lower() and 'email' in str(e).lower():
                    messages.error(request, 'This email is already registered. Please use another email.')
                else:
                    # หากเป็น IntegrityError อื่นๆ
                    messages.error(request, 'There was an error creating your account. Please try again.')
                
                # รีเทิร์นไปที่หน้า register พร้อมฟอร์มเดิม
                return render(request, 'register.html', {'form': form})
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def login_views(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Logged in successfully!')

            if user.is_staff:
                return redirect('/admin/')
            else:
                try:
                    custom_user = User.objects.get(user=user.username)
                    request.session['user_id'] = custom_user.user_id
                except User.DoesNotExist:
                    messages.error(request, 'User not found in the database.')
                    return redirect('login')
                return redirect('/folder')
        else:
            # form ไม่ valid: แยกกรณีว่า username นี้มีอยู่หรือไม่
            try:
                custom_user = User.objects.get(user=username)
                # พบ user ในระบบ แปลว่าพิมพ์รหัสผ่านผิด
                messages.error(request, 'Invalid Password')
            except User.DoesNotExist:
                # ไม่พบ user หมายความว่า username ไม่ถูก
                messages.error(request, 'Invalid Username')

            return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_views(request):
    logout(request)
    messages.info(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def profile_view(request):
    user_id = request.session.get('user_id')  # ดึง user_id จาก session ที่เก็บไว้ตอน login

    try:
        custom_user = User.objects.get(user_id=user_id)  # ดึงข้อมูลจากโมเดล User โดยใช้ user_id
        auth_user = request.user  # Django auth user
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login')

    if request.method == 'POST':
        # รับข้อมูลใหม่จากผู้ใช้แล้วอัปเดต
        new_username = request.POST.get('user')
        new_fname = request.POST.get('fname')
        new_lname = request.POST.get('lname')
        new_title = request.POST.get('title')
        new_card_color = request.POST.get('card_color')
        new_email = request.POST.get('email')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        # ตรวจสอบว่าชื่อผู้ใช้ใหม่ซ้ำหรือไม่
        if auth_user.username != new_username and User.objects.filter(user=new_username).exists():
            messages.error(request, 'Username already exists. Please choose a different one.')
            return redirect('profile')

        # อัปเดตข้อมูลใน custom User
        custom_user.user = new_username
        custom_user.fname = new_fname
        custom_user.lname = new_lname
        custom_user.title = new_title
        custom_user.card_color = new_card_color
        custom_user.email = new_email
        if 'profile_picture' in request.FILES:
            custom_user.profile_picture = request.FILES['profile_picture']
        custom_user.save()

        # อัปเดตข้อมูลใน auth User (Django default User model)
        auth_user.username = new_username
        auth_user.first_name = new_fname
        auth_user.last_name = new_lname
        auth_user.email = new_email

        # หากผู้ใช้กรอก new_password ให้ทำการตรวจสอบรหัสผ่านปัจจุบันก่อนเปลี่ยน
        if new_password:
            if not auth_user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile')
            auth_user.set_password(new_password)  # เปลี่ยนรหัสผ่านและเข้ารหัส

        auth_user.save()

        # อัปเดต session authentication hash เพื่อให้ผู้ใช้ยังคงเข้าสู่ระบบอยู่หลังจากเปลี่ยนข้อมูล
        update_session_auth_hash(request, auth_user)

        messages.success(request, 'Profile updated successfully!')
        return redirect('folder')

    context = {
        'user': custom_user,
    }
    return render(request, 'profile.html', context)
