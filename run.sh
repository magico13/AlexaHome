sudo docker rm alexa
sudo docker run -d --name alexa -p 443:443 alexaserver
#sudo docker run -it --name alexa -p 443:443 --rm alexaserver /bin/bash
