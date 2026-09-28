from django.urls import reverse


def _nav_items(user):
    if not user.is_authenticated:
        return []

    items = [
        {"label": "Dashboard", "url": reverse("dashboard:home"), "icon": "speedometer2"},
        {"label": "Leads", "url": reverse("leads:list"), "icon": "person-lines-fill"},
        {"label": "Follow-ups", "url": reverse("leads:followup_queue"), "icon": "clock-history"},
        {"label": "Admissions", "url": reverse("admissions:list"), "icon": "mortarboard"},
    ]

    if user.role in ("CLIENT_ADMIN", "SUPER_ADMIN"):
        items.append({"label": "Staff", "url": reverse("accounts:staff_list"), "icon": "people"})
        items.append({"label": "Campaigns", "url": reverse("campaigns:list"), "icon": "megaphone"})
        items.append({"label": "Audit Log", "url": reverse("audit:list"), "icon": "journal-text"})

    if user.role == "SUPER_ADMIN":
        items.append({"label": "Clients", "url": reverse("clients:list"), "icon": "building"})
        items.append({"label": "Import CSV", "url": reverse("csv_import:upload"), "icon": "upload"})
        items.append({"label": "WhatsApp", "url": reverse("whatsapp:inbox"), "icon": "whatsapp"})

    return items


def navigation(request):
    user = getattr(request, "user", None)
    if user is None:
        return {}
    items = _nav_items(user)

    # Longest matching prefix wins, so '/leads/followups/' highlights "Follow-ups"
    # rather than the more general "Leads" item.
    matches = [item for item in items if request.path.startswith(item["url"])]
    current = max(matches, key=lambda item: len(item["url"])) if matches else None

    return {
        "nav_items": items,
        "page_heading": current["label"] if current else "Dashboard",
        "active_nav_url": current["url"] if current else None,
    }
