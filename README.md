# Out of Band Monitoring

# Dependency package.
$ pip3 install -r requirements.txt

# Deployment
## Run it as a foreground applicaiton with nohup, tmux or screen
Logging as any user, run below commands.
$ nohup python3 daemon.py &  

## Run it as systemd service.
copy the oob_monitoring.service to /etc/systemd/system/ folder.
If physically it is in the same partition, you can create a link to that file.
$ systemctl enable oob_monitoring
$ systemctl start oob_monitoring



