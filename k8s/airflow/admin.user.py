#!/usr/bin/env python3
import airflow
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
user = PasswordUser(models.User())
user.username = 'admin'
user.email = 'admin@example.com'
user.password = 'change_me'
session = settings.Session()
if not session.query(PasswordUser).filter(PasswordUser.username == user.username).first():
  print('Adding Admin user')
  session.add(user)
  session.commit()
else:
  print('Admin User exists')
session.close()
exit()
