from . import models

from django.contrib.auth import mixins


class Owner(mixins.PermissionRequiredMixin):
    def has_permission(self):
        return self.request.user == self.get_object().owner


class CalendarPermissionRequired(mixins.PermissionRequiredMixin):
    def has_permission(self):
        try:
            self.calendar = models.Calendar.objects.get(
                pk=self.kwargs["calendar"],
                owner_id=self.request.user.id,
            )
        except models.Calendar.DoesNotExist:
            return False
        else:
            return True


class CalendarOrPublicRequired(mixins.PermissionRequiredMixin):
    def has_permission(self):
        try:
            self.calendar = models.Calendar.objects.get(
                pk=self.kwargs["calendar"],
            )
        except models.Calendar.DoesNotExist:
            return False
        else:
            return (
                self.request.user.id == self.calendar.owner.id or self.calendar.public
            )

    def get_template_names(self):
        if self.request.user == self.calendar.owner:
            return super().get_template_names()
        return [self.template_public]


class LoggedinOrPublic(mixins.PermissionRequiredMixin):
    def has_permission(self):
        self.object = self.get_object()
        if self.request.user == self.object.owner:
            return True
        return self.object.public

    def get_template_names(self):
        names = super().get_template_names()
        if self.request.user == self.object.owner:
            return names
        return [self.template_public]
