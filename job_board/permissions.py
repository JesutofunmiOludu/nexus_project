from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner`, `user`, or `employer` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        
        # 1. Check if the object is the User model itself
        if hasattr(obj, 'email') and hasattr(obj, 'role'): 
             # obj is likely the User instance
             return obj == request.user

        # 2. Check for 'user' attribute (Profiles, SavedJob, etc.)
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # 3. Check for 'employer' attribute (Company, Job)
        # Note: obj.employer is an EmployerProfile, so we check obj.employer.user
        if hasattr(obj, 'employer'):
            return obj.employer.user == request.user
            
        # 4. Check for 'freelancer' attribute (Reviews)
        if hasattr(obj, 'freelancer'):
            # If it's a review, usually the AUTHOR (employer) should edit it, not the subject (freelancer).
            # We might need a separate check for Reviews if we want the author to edit.
            # For now, let's assume this handles cases where the freelancer owns the object.
            return obj.freelancer.user == request.user

        return False


class IsEmployer(permissions.BasePermission):
    """
    Allows access only to users with the 'employer' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'employer')


class IsFreelancer(permissions.BasePermission):
    """
    Allows access only to users with the 'freelancer' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'freelancer')
