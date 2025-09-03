from django.contrib.auth.views import LoginView
from django.conf import settings

class InstructorLoginView(LoginView):
    template_name = "instructor_portal/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/instructor/"

    def form_valid(self, form):
        # Make instructor session cookie unique
        self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        self.request.session['portal'] = 'instructor'
        return super().form_valid(form)
