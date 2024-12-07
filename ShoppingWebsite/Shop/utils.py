from django.core.exceptions import PermissionDenied


def superuser_required(view_func):
    def wrap(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("You do not have access to this page.")
        return view_func(request, *args, **kwargs)

    return wrap
