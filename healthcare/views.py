from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home(request):
    """Landing page view."""
    return render(request, 'home.html')

@login_required
def dashboard(request):
    """Main dashboard view that redirects to role-specific dashboards."""
    if request.user.role == 'PATIENT':
        return redirect('patients:dashboard')
    elif request.user.role == 'DOCTOR':
        return redirect('doctors:dashboard')
    elif request.user.role == 'LAB_ATTENDANT':
        return redirect('lab:lab_attendant_dashboard')
    return redirect('login') 