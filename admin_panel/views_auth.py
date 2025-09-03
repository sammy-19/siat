from django.contrib.auth.views import LoginView
from django.conf import settings

class AdminLoginView(LoginView):
    template_name = "admin_panel/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/admin_panel/"

    def form_valid(self, form):
        # Make admin session cookie unique
        self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        self.request.session['portal'] = 'admin'
        return super().form_valid(form)
