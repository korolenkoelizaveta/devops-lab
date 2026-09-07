from django.views.generic import TemplateView
from typing import Any
from gym.models import User


class ShowTrainerView(TemplateView):
    template_name = "trainers/show_trainers.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["trainers"] = User.objects.filter(role="trainer")
        return context
