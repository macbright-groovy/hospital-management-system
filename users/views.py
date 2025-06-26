from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import UserRegistrationForm, UserProfileUpdateForm
from .models import User, PatientProfile, DoctorProfile, LabAttendantProfile
from doctors.models import Doctor

# Create your views here.

# User registration view
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the user
                    user = form.save()
                    
                    # Create role-specific profile
                    role = form.cleaned_data.get('role')
                    if role == User.Role.PATIENT:
                        date_of_birth = request.POST.get('date_of_birth')
                        PatientProfile.objects.create(
                            user=user,
                            date_of_birth=date_of_birth
                        )
                    elif role == User.Role.DOCTOR:
                        specialty = request.POST.get('specialty')
                        # Create DoctorProfile
                        DoctorProfile.objects.create(
                            user=user,
                            specialty=specialty
                        )
                        # Create Doctor instance
                        Doctor.objects.create(
                            user=user,
                            specialization=specialty,
                            license_number=request.POST.get('license_number', ''),
                            years_of_experience=0
                        )
                    elif role == User.Role.LAB_ATTENDANT:
                        lab_name = request.POST.get('lab_name')
                        LabAttendantProfile.objects.create(
                            user=user,
                            lab_name=lab_name
                        )
                    
                    # Do NOT log the user in
                    messages.success(request, 'Registration successful! You can now log in.')
                    return redirect('users:login')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
                return render(request, 'users/register.html', {'form': form})
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

# User login view
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect based on role
            if user.role == User.Role.PATIENT:
                return redirect('patients:dashboard')
            elif user.role == User.Role.DOCTOR:
                return redirect('doctors:dashboard')
            elif user.role == User.Role.LAB_ATTENDANT:
                return redirect('lab:lab_attendant_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'users/login.html')

# User logout view
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

# Move profile view to patients app
# @login_required
# def profile(request):
#     if request.method == 'POST':
#         form = UserProfileUpdateForm(request.POST, instance=request.user)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     user = form.save()
#                     
#                     # Update role-specific profile
#                     if user.role == User.Role.PATIENT:
#                         profile = user.patient_profile
#                         profile.date_of_birth = request.POST.get('date_of_birth')
#                         profile.save()
#                     elif user.role == User.Role.DOCTOR:
#                         profile = user.doctor_profile
#                         profile.specialty = request.POST.get('specialty')
#                         profile.save()
#                     elif user.role == User.Role.LAB_ATTENDANT:
#                         profile = user.lab_attendant_profile
#                         profile.lab_name = request.POST.get('lab_name')
#                         profile.save()
#                     
#                     messages.success(request, 'Profile updated successfully!')
#                     return redirect('profile')
#             except Exception as e:
#                 messages.error(request, f'An error occurred while updating profile: {str(e)}')
#     else:
#         form = UserProfileUpdateForm(instance=request.user)
#         
#         # Add role-specific data to the form
#         if request.user.role == User.Role.PATIENT:
#             form.initial['date_of_birth'] = request.user.patient_profile.date_of_birth
#         elif request.user.role == User.Role.DOCTOR:
#             form.initial['specialty'] = request.user.doctor_profile.specialty
#         elif request.user.role == User.Role.LAB_ATTENDANT:
#             form.initial['lab_name'] = request.user.lab_attendant_profile.lab_name
#     
#     return render(request, 'users/profile.html', {
#         'form': form,
#         'user': request.user
#     })
