from django.core.management.base import BaseCommand
from apps.account.models import Permission, Role
from apps.account.rbac import create_permission, create_role


class Command(BaseCommand):
    help = 'Initialize default RBAC permissions and roles'

    def handle(self, *args, **options):
        self.stdout.write('Initializing RBAC system...')
        
        # Create default permissions
        permissions_data = [
            # User Management
            {'code': 'create_users', 'name': 'Create Users', 'description': 'Can create new users', 'category': 'user_management'},
            {'code': 'view_users', 'name': 'View Users', 'description': 'Can view user list', 'category': 'user_management'},
            {'code': 'edit_users', 'name': 'Edit Users', 'description': 'Can edit user information', 'category': 'user_management'},
            {'code': 'delete_users', 'name': 'Delete Users', 'description': 'Can delete users', 'category': 'user_management'},
            
            # Role Management
            {'code': 'manage_roles', 'name': 'Manage Roles', 'description': 'Can create, edit, and delete roles', 'category': 'role_management'},
            {'code': 'assign_roles', 'name': 'Assign Roles', 'description': 'Can assign roles to users', 'category': 'role_management'},
            {'code': 'view_user_roles', 'name': 'View User Roles', 'description': 'Can view user role assignments', 'category': 'role_management'},
            
            # Permission Management
            {'code': 'manage_permissions', 'name': 'Manage Permissions', 'description': 'Can create, edit, and delete permissions', 'category': 'permission_management'},
            {'code': 'view_permissions', 'name': 'View Permissions', 'description': 'Can view permissions', 'category': 'permission_management'},
            
            # Dashboard
            {'code': 'view_dashboard', 'name': 'View Dashboard', 'description': 'Can access dashboard', 'category': 'dashboard'},
            {'code': 'customize_dashboard', 'name': 'Customize Dashboard', 'description': 'Can customize dashboard layout', 'category': 'dashboard'},
            
            # Content Management
            {'code': 'view_content', 'name': 'View Content', 'description': 'Can view content', 'category': 'content'},
            {'code': 'edit_content', 'name': 'Edit Content', 'description': 'Can edit content', 'category': 'content'},
            {'code': 'delete_content', 'name': 'Delete Content', 'description': 'Can delete content', 'category': 'content'},
            {'code': 'publish_content', 'name': 'Publish Content', 'description': 'Can publish content', 'category': 'content'},
            
            # Reports
            {'code': 'view_reports', 'name': 'View Reports', 'description': 'Can view reports', 'category': 'reports'},
            {'code': 'generate_reports', 'name': 'Generate Reports', 'description': 'Can generate reports', 'category': 'reports'},
            {'code': 'export_reports', 'name': 'Export Reports', 'description': 'Can export reports', 'category': 'reports'},
        ]
        
        created_permissions = []
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults=perm_data
            )
            if created:
                created_permissions.append(permission)
                self.stdout.write(f'Created permission: {permission.name}')
            else:
                created_permissions.append(permission)
        
        # Create default roles
        roles_data = [
            {
                'name': 'Admin',
                'display_name': 'Administrator',
                'description': 'Full system access',
                'permissions': [p for p in created_permissions],  # All permissions
                'dashboard_config': {
                    'layout': 'grid',
                    'widgets': [
                        {'type': 'user_stats', 'title': 'User Statistics', 'size': 'large'},
                        {'type': 'recent_activity', 'title': 'Recent Activity', 'size': 'medium'},
                        {'type': 'system_health', 'title': 'System Health', 'size': 'medium'},
                        {'type': 'quick_actions', 'title': 'Quick Actions', 'size': 'small'},
                    ],
                    'theme': 'admin',
                    'columns': 3
                }
            },
            {
                'name': 'Manager',
                'display_name': 'Manager',
                'description': 'Management level access',
                'permissions': [p for p in created_permissions if p.category in ['user_management', 'role_management', 'dashboard', 'content', 'reports']],
                'dashboard_config': {
                    'layout': 'grid',
                    'widgets': [
                        {'type': 'team_stats', 'title': 'Team Statistics', 'size': 'large'},
                        {'type': 'recent_activity', 'title': 'Recent Activity', 'size': 'medium'},
                        {'type': 'quick_actions', 'title': 'Quick Actions', 'size': 'small'},
                    ],
                    'theme': 'manager',
                    'columns': 2
                }
            },
            {
                'name': 'Editor',
                'display_name': 'Content Editor',
                'description': 'Content management access',
                'permissions': [p for p in created_permissions if p.category in ['content', 'dashboard']],
                'dashboard_config': {
                    'layout': 'grid',
                    'widgets': [
                        {'type': 'content_stats', 'title': 'Content Statistics', 'size': 'large'},
                        {'type': 'recent_content', 'title': 'Recent Content', 'size': 'medium'},
                        {'type': 'drafts', 'title': 'Drafts', 'size': 'small'},
                    ],
                    'theme': 'editor',
                    'columns': 2
                }
            },
            {
                'name': 'Viewer',
                'display_name': 'Viewer',
                'description': 'Read-only access',
                'permissions': [p for p in created_permissions if p.code in ['view_dashboard', 'view_content', 'view_reports']],
                'dashboard_config': {
                    'layout': 'grid',
                    'widgets': [
                        {'type': 'content_overview', 'title': 'Content Overview', 'size': 'large'},
                        {'type': 'recent_activity', 'title': 'Recent Activity', 'size': 'medium'},
                    ],
                    'theme': 'viewer',
                    'columns': 2
                }
            }
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data['description'],
                    'dashboard_config': role_data['dashboard_config']
                }
            )
            
            if created:
                role.permissions.set(role_data['permissions'])
                self.stdout.write(f'Created role: {role.display_name}')
            else:
                self.stdout.write(f'Role already exists: {role.display_name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully initialized RBAC system!')
        )
