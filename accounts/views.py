from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

@login_required
def profile_view(request):
    """
    Displays and allows editing of user profile details.
    """
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        messages.success(request, 'Your profile details have been successfully updated.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'user': user})


@login_required
def change_password_view(request):
    """
    Handles user password change with standard Django security form.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
