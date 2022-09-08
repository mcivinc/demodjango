from django.contrib.auth.models import AbstractUser


class MCIVUser(AbstractUser):
    def process_something(self, groups):
        print(">>>>> process_something")


