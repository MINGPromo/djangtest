def auth_roles(request):
    """
    Universally provide user role flags and permissions to all templates.
    Avoids brittle template checks like `user.groups.all.0.name`.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "is_admin": False,
            "is_staff_role": False,
            "is_requester": False,
            "is_executor": False,
            "user_group_names": [],
        }

    user = request.user
    group_names = set(user.groups.values_list("name", flat=True))
    is_admin = bool(user.is_superuser or "admin" in group_names)
    is_staff_role = bool(is_admin or "staff" in group_names)
    is_requester = bool(is_admin or "requester" in group_names)
    is_executor = bool(is_admin or "executor" in group_names)

    return {
        "is_admin": is_admin,
        "is_staff_role": is_staff_role,
        "is_requester": is_requester,
        "is_executor": is_executor,
        "user_group_names": list(group_names),
    }
