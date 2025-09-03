from django.contrib.auth.views import LoginView
from django.conf import settings

class StudentLoginView(LoginView):
    template_name = "student_portal/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/portal/"

    def form_valid(self, form):
        # Make student session cookie unique
        self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        self.request.session['portal'] = 'student'
        return super().form_valid(form)
