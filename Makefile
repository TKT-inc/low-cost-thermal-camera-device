run:
	echo 'khoa1234' | sudo -S systemctl restart nvargus-daemon.service
	python3 device_app/device_app_main.py

resetcam:
	echo 'khoa1234' | sudo -S systemctl restart nvargus-daemon.service

transform:
	python3 set_up/get_bounding_homo.py

cv:
	workon cv