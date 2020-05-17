from rest_framework import authentication


class BasicAuthentication(authentication.BasicAuthentication):
    def authenticate_credentials(self, userid, password, request=None):
        if "@" in userid:
            userid, domain = userid.split("@")
            print(userid, domain)
        return super().authenticate_credentials(userid, password, request)
