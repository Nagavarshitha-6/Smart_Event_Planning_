from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/', include('accounts.urls')),
    
    # Core Platform Modules
    path('', include('dashboard.urls')),
    path('events/', include('events.urls')),
    path('registrations/', include('registrations.urls')),
    path('attendance/', include('attendance.urls')),
    path('vendors/', include('vendors.urls')),
    path('resources/', include('resources.urls')),
    path('budgets/', include('budgets.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
