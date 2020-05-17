from setuptools import find_packages, setup

setup(
    name="todo-django",
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    include_package_data=True,
    license="MIT License",
    description="A simple stats package",
    url="https://github.com/todo/todo-django",
    author="Paul Traylor",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP",
    ],
    install_requires=[
        "Django>=3.0",
        "djangorestframework",
        "djangorestframework-xml",
        "icalendar",
        "python-dateutil",
        "pytz",
    ],
    extras_require={
        "standalone": [
            "django-environ",
            "prometheus-client",
            "sentry_sdk",
        ],
        "dev": [
            "black",
            "codecov",
            "django-nose",
            "flake8",
            "nose-cov",
            "psycopg2-binary",
            "unittest-xml-reporting",
        ],
    },
    entry_points={
        "console_scripts": ["todo-server = todo.standalone.manage:main"],
    },
)
