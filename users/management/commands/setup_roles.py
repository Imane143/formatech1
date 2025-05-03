from django.core.management.base import BaseCommand
from users.models import Role, Permission, RolePermission, User

class Command(BaseCommand):
    help = 'Sets up default roles and permissions'

    def handle(self, *args, **kwargs):
        # Create roles if they don't exist
        admin_role, created = Role.objects.get_or_create(
            name="Admin",
            defaults={"description": "Full access to all features"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Admin role created'))
        
        user_role, created = Role.objects.get_or_create(
            name="User",
            defaults={"description": "Limited access to features"}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('User role created'))
        
        # Create permissions
        permissions = [
            ("manage_trainings", "Manage Trainings", "Can create, update, and delete training programs"),
            ("manage_sessions", "Manage Sessions", "Can create, update, and delete training sessions"),
            ("manage_trainers", "Manage Trainers", "Can assign trainers to sessions"),
            ("generate_certificates", "Generate Certificates", "Can generate certificates for participants"),
            ("view_reports", "View Reports", "Can view and export reports"),
            ("participate_trainings", "Participate in Trainings", "Can register for training sessions"),
            ("view_certificates", "View Certificates", "Can view own certificates"),
        ]
        
        for code, name, description in permissions:
            perm, created = Permission.objects.get_or_create(
                code=code,
                defaults={"name": name, "description": description}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Permission {name} created'))
                
            # Assign all permissions to Admin
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
            
            # Assign limited permissions to User
            if code in ['participate_trainings', 'view_certificates']:
                RolePermission.objects.get_or_create(role=user_role, permission=perm)
        
        # Make sure existing staff users have admin role
        for user in User.objects.filter(is_staff=True, role__isnull=True):
            user.role = admin_role
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Assigned Admin role to {user.username}'))
        
        # Assign user role to all other users without a role
        for user in User.objects.filter(is_staff=False, role__isnull=True):
            user.role = user_role
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Assigned User role to {user.username}'))