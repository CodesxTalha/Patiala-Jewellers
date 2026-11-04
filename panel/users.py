"""Users: the people who can sign in to this panel. An Owner can do everything, including managing users. An Editor can edit the site but not the users."""
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

User = get_user_model()
ROLES = [("owner", "Owner", "Can do everything, including adding and removing users."),
         ("editor", "Editor", "Can edit the whole site and read enquiries, but cannot manage users.")]


def _owner_only(request):
    return None if request.user.is_superuser else JsonResponse({"error": "Only an owner can manage users."}, status=403)


def role_of(user):
    return "owner" if user.is_superuser else "editor"


def _owners_left(excluding=None):
    return User.objects.filter(is_superuser=True, is_active=True).exclude(pk=excluding).count()


def listing(request, site):
    if (denied := _owner_only(request)):
        return denied
    users = list(User.objects.order_by("-is_superuser", "username"))
    for u in users:
        u.role = role_of(u)
        u.display = u.get_full_name() or u.username
    context = dict(site.each_context(request), title="Users", users=users)
    return render(request, "admin/users.html", context)


def editor(request, site, pk=None):
    if (denied := _owner_only(request)):
        return denied
    person = get_object_or_404(User, pk=pk) if pk else None
    is_me = bool(person and person.pk == request.user.pk)
    data = {"first_name": person.first_name if person else "", "last_name": person.last_name if person else "",
            "username": person.username if person else "", "email": person.email if person else "",
            "role": role_of(person) if person else "editor", "is_active": person.is_active if person else True}
    errors = {}
    if request.method == "POST":
        post = request.POST
        data.update(first_name=strip_tags(post.get("first_name", "")).strip()[:150], last_name=strip_tags(post.get("last_name", "")).strip()[:150],
                    username=post.get("username", "").strip(), email=post.get("email", "").strip()[:254])
        if not is_me:
            data.update(role="owner" if post.get("role") == "owner" else "editor", is_active="is_active" in post)
        password = post.get("password", "")
        if not data["username"]:
            errors["username"] = "Choose a username to sign in with."
        elif len(data["username"]) > 150 or not all(ch.isalnum() or ch in "@.+-_" for ch in data["username"]):
            errors["username"] = "Use letters, numbers and @ . + - _ only."
        elif User.objects.filter(username__iexact=data["username"]).exclude(pk=pk).exists():
            errors["username"] = "Someone already uses this username."
        if data["email"] and "@" not in data["email"]:
            errors["email"] = "That does not look like an email address."
        if not person and not password:
            errors["password"] = "Set a password for them."
        if password:
            try:
                validate_password(password, user=person or User(username=data["username"], email=data["email"]))
            except ValidationError as e:
                errors["password"] = " ".join(e.messages)
        if person and not is_me and person.is_superuser and (data["role"] != "owner" or not data["is_active"]) and _owners_left(person.pk) == 0:
            errors["role"] = "There must always be one active owner."
        if not errors:
            user = person or User()
            user.first_name, user.last_name, user.username, user.email = data["first_name"], data["last_name"], data["username"], data["email"]
            if not is_me:
                user.is_superuser, user.is_active = data["role"] == "owner", data["is_active"]
            user.is_staff = True                    # everyone here can sign in to the panel
            if password:
                user.set_password(password)
            user.save()
            user.user_permissions.set([] if user.is_superuser else Permission.objects.filter(content_type__app_label__in=("shop", "panel")).exclude(
                content_type__app_label="panel", codename__startswith="delete"))
            if is_me and password:
                update_session_auth_hash(request, user)
            messages.success(request, f"{user.get_full_name() or user.username} saved.")
            return redirect("admin:users")
    context = dict(site.each_context(request), title=(person.get_full_name() or person.username) if person else "New user", person=person, is_me=is_me,
                   data=data, errors=errors, roles=ROLES, can_delete=bool(person and not is_me))
    return render(request, "admin/user_form.html", context)


@require_POST
def delete(request, pk):
    if (denied := _owner_only(request)):
        return denied
    person = get_object_or_404(User, pk=pk)
    if person.pk == request.user.pk:
        messages.error(request, "You cannot delete the account you are using.")
        return redirect("admin:user_edit", pk)
    if person.is_superuser and _owners_left(person.pk) == 0:
        messages.error(request, "There must always be one active owner.")
        return redirect("admin:user_edit", pk)
    name = person.get_full_name() or person.username
    person.delete()
    messages.success(request, f"{name} was removed.")
    return redirect("admin:users")
