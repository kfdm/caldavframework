from setuptools import find_packages, setup

setup(
    name="todo",
    author="Paul Traylor",
    url="http://github.com/kfdm/todo/",
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "dj-database-url==0.4.2",
        "Django==2.0.6",
        "djangorestframework==3.8.2",
        "envdir==1.0.1",
        "prometheus_client",
        "pytz",
        "raven",
        "requests",
        "django-rest-swagger",
        "social-auth-app-django==2.1.0",
        "coreapi",
    ],
    entry_points={"console_scripts": ["todo-server = todo.manage:main"]},
)
