from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from blog.models import Post, Comment

class Command(BaseCommand):
    help = 'Initialize Administrators, Users, and Guests user groups and their permissions'

    def handle(self, *args, **options):
        groups_config = {
            'Administrators': {
                'permissions': [
                    'add_post', 'change_post', 'delete_post', 'view_post',
                    'add_comment', 'view_comment'
                ],
                'desc': 'Administrator group'
            },
            'Users': {
                'permissions': ['add_comment', 'view_comment'],
                'desc': 'Regular User Group'
            },
            'Guests': {
                'permissions': ['view_post', 'view_comment'],
                'desc': 'Read-Only Guest Group'
            }
        }

        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            group.permissions.clear()
            
            for codename in config['permissions']:
                try:
                    permission = Permission.objects.get(codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Warning: Permission {codename} does not exist'))

            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created group: {group_name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Successfully updated group permissions: {group_name}'))

        self.stdout.write(self.style.SUCCESS('User group permissions initialized successfully!'))