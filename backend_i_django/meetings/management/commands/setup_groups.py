from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from meetings.models import ActionItem, Meeting


class Command(BaseCommand):
    help = "Create admin, editor, and viewer groups with appropriate permissions."

    def handle(self, *args, **kwargs) -> None:
        meeting_ct = ContentType.objects.get_for_model(Meeting)
        action_item_ct = ContentType.objects.get_for_model(ActionItem)

        all_perms = Permission.objects.filter(content_type__in=[meeting_ct, action_item_ct])
        no_delete_perms = all_perms.exclude(codename__startswith="delete_")
        view_only_perms = all_perms.filter(codename__startswith="view_")

        admin_group, _ = Group.objects.get_or_create(name="admin")
        admin_group.permissions.set(all_perms)

        editor_group, _ = Group.objects.get_or_create(name="editor")
        editor_group.permissions.set(no_delete_perms)

        viewer_group, _ = Group.objects.get_or_create(name="viewer")
        viewer_group.permissions.set(view_only_perms)

        self.stdout.write(self.style.SUCCESS("Groups created: admin, editor, viewer"))
        for group in [admin_group, editor_group, viewer_group]:
            perms = ", ".join(group.permissions.values_list("codename", flat=True))
            self.stdout.write(f"  {group.name}: {perms}")
