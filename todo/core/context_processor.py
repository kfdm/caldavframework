import datetime

from todo.core import models


def navigation(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "today": datetime.date.today(),
        "project_list": models.Project.objects.filter(owner=request.user),
        "search_list": models.Search.objects.filter(owner=request.user),
    }
