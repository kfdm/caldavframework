migrate:
	todo-server makemigrations
	todo-server migrate

revert:
	todo-server migrate core zero 
	rm todo/core/migrations/0001_initial.py
