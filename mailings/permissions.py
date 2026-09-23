from django.contrib.auth.mixins import UserPassesTestMixin


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().owner == self.request.user