# pages/context_processors.py

import logging

from django.contrib.auth.models import User

from enrollment.models.enrollment import ActiveEnrollment
from faction.models.faction import Faction
from .menus import (
    FACULTY_ADMIN_MENU,
    ATTENDEE_MENU,
    LEADER_MENU,
    LEADER_ADMIN_MENU,
    FACULTY_MENU,
    ORGANIZATION_FACULTY_MENU,
    toplinks,
)

logger = logging.getLogger(__name__)


def build_dynamic_url(item, user):
    if "dynamic_params" in item:
        for key, path in item["dynamic_params"].items():
            if path:
                logger.debug(f"Processing dynamic param: {path}")
                value = user
                for attr in path.split("."):
                    value = getattr(value, attr, None)
                    if value is None:
                        logger.warning(f"Attribute '{attr}' in '{path}' is None.")
                        break
                item["dynamic_params"][key] = value
            else:
                logger.warning(f"Dynamic param for key '{key}' is None.")
                item["dynamic_params"][key] = None
    return item



def dynamic_menu(request):
    menu = []
    if request.user.is_authenticated:
        user = request.user
        user_type = user.user_type
        menu_mapping = {
            "FACULTY": FACULTY_MENU,
            "ATTENDEE": ATTENDEE_MENU,
            "LEADER": LEADER_MENU,
            "ORGANIZATION_FACULTY": ORGANIZATION_FACULTY_MENU,
        }
        if user_type == "FACULTY" and user.is_admin:
            menu = FACULTY_ADMIN_MENU.copy()
        elif user_type == "LEADER" and user.is_admin:
            menu = LEADER_ADMIN_MENU.copy()
        else:
            menu = menu_mapping.get(user_type, []).copy()

        context = {"user": user}
        # Add any additional context needed for dynamic params
        if hasattr(user, 'facultyprofile'):
            context['faculty_slug'] = user.facultyprofile.facility.slug

        for item in menu:
            item = build_dynamic_url(item, user)

            if "sub_items" in item:
                for sub_item in item["sub_items"]:
                    sub_item = build_dynamic_url(sub_item, user)

        logger.debug(f"menu: {menu}")

    return {"menu_items": menu}



def top_links_menu(request):
    context = {"toplinks": toplinks}
    logger.debug("Top links menu context: %s", context)
    return context


def user_type(request):
    return {
        "user_type": (
            request.user.user_type if request.user.is_authenticated else "other"
        )
    }


def user_profile(request):
    if request.user.is_authenticated:
        return {"user_profile": request.user.get_profile()}
    else:
        return {"user_profile": []}


def active_enrollment(request):
    if request.user.is_superuser:
        return {}
    if active_enrollment_id := request.session.get("active_enrollment_id"):
        active_enrollment = ActiveEnrollment.objects.get(id=active_enrollment_id)
    elif request.user.is_authenticated:
        active_enrollment = ActiveEnrollment.objects.get(
            user_id=request.user.id
        ) or ActiveEnrollment(user_id=request.user.id)
    else:
        active_enrollment = ActiveEnrollment()
    faction_enrollment = active_enrollment.faction_enrollment or {}
    if faction_enrollment:
        faction_id = active_enrollment.faction_enrollment.faction.id or 0
        faction = (
            Faction.objects.with_member_count()
            .with_sub_faction_count()
            .get(id=faction_id)
        )
        active_enrollment.faction_enrollment.faction = faction

    return {"active_enrollment": active_enrollment}


def color_scheme_processor(request):
    """Returns a dictionary containing the color scheme for the website."""

    warm_orange = "#ea6900"
    deep_red = "#cc2500"
    earthy_brown = "#612809"
    creamy_white = "#fff8db"
    forest_green = "#556643"
    dark_charcoal = "#00100c"

    highlight = warm_orange
    call_to_action = deep_red
    bg_dk = earthy_brown
    bg_lt = creamy_white
    secondary = forest_green
    text = dark_charcoal

    colors = {
        "text": text,
        "bg_lt": bg_lt,
        "bg_dk": bg_dk,
        "secondary_highlight": secondary,
        "call_to_action": call_to_action,
        "primary": highlight,
    }

    return {"color_scheme": colors}
