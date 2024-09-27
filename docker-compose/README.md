# Docker compose setup：

The setup.py script will set up a compose project named docker-compose, which  
includs three services, named openikt-db, openikt-server and openikt-web.  

 - openikt-db: the Postgres database
 - openikt-server: the Django project
 - openikt-web: Nginx web server works as a proxy and for serving static content

## Deployment files and descriptions:

```shell
docker-compose/  
├── compose.yml.j2 # The Jinja2 template file of compose.yml, used to render  
                   # compose.yml, you can change it if necessary.  
├── Dockerfile.server # The Dockerfile used to build the image for the  
                      # openikt-server container  
├── Dockerfile.web # The Dockerfile used to build the image for the openikt-web  
                   # container  
├── nginx-web.conf.j2 # The Jinja2 template file of nginx-web.conf, which is used  
                      # for openikt-web, change it if necessary.  
├── README # The documentation file  
├── setup.py # The setup script  
└── uwsgi.ini # The uWSGI configuration file for starting the Django project  
              # in the openikt-server container  
└── ssl # Directory where cert and cert private key files are stored  
```

## Prerequisites：

1. Install Docker 20.10 or higher version, for installation instructions please  
   refer to: https://docs.docker.com/compose/install/. The setup.py script uses  
   the docker compose command, which is available on Docker 20.10 or higher version.  
   Check Docker version using: docker --version  
  
   If you are a non-root user on your host, to ensure setup.py run correctly  
   without sudo, you need to execute the following command to add user to docker  
   group: sudo usermod -aG docker username  
  
2. The setup.py will automatically install the jinja2 module, which is required  
   by the script. And make sure that you are currently using a virtual environment.  
     
   Install manually using pip: pip install jinja2  
  
## Installation steps：  
  
1. Clone the repository:    
   git clone https://github.com/intel/openikt.git  
  
2. There are some default behaviors of the setup.py script that you should be  
   aware of in advance. Please refer to './setup.py install --help' for more information  
  
   The example installation command:    
   ./setup.py install --port 80 --data-dir ~/app/postgres --web-log-dir ~/app/logs/web \  
                      --server-log-dir ~/app/logs/server  
  
   enable https and put the cert, private key file in ssl directory:  
   ./setup.py install --port 80 --data-dir ~/app/postgres --web-log-dir ~/app/logs/web \  
                      --server-log-dir ~/app/logs/server --enable-https \  
                      --nginx-servername www.mydomain.com --cert ssl/mycert.crt \  
                      --cert-key ssl/mycert.key  
  
3. Access the service at:    
   http://host-ip   
   or  
   https://www.mydomain.com  
  
## Update service/container  
  
The setup.py script can also be used to update container services. If you have made  
any change, you can use this script to apply the updates to the services. Of course,   
if you are familiar with Docker Compose, you can also deploy updates using Docker  
Compose commands directly.  
  
The example update command:  
./setup.py update --service openikt-web  
  
For more information, refer to: './setup.py update --help  
  
## Uninstall service  
  
You can use uninstall command to wipe out any existing data in the database, application  
logs and uninstall all the application with option --remove-data. Also you can retain the  
data in the database and the application logs with no any option.  
  
The example uninstall command:  
./setup.py uninstall --remove-data  
or  
./setup.py uninstall  
