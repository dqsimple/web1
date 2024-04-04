from functools import wraps
from .models import ActionLog, User

def log_Ation(action):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            print(dir(request))
            print(request.user)
            #user = request.user if request.user.is_authenticated else None
            user = request.user if request.user else None
            if user:
                tem_user = User.objects.filter(username=user)
                print(tem_user)
                if tem_user:
                    user = User.objects.get(username=user)
                    print(user.u_id)
                    print(user)
                    ActionLog.objects.create(user=user, action=action)
            return response
        return _wrapped_view
    return decorator