# Overview

This is a repository that contains all the code for OpenIKT(Open Inter kernel Tools). OpenIKT is a batch of utility tools, used to track the kernel patch status among multi open-source projects. it is developed by the Django and VUE. 



# Quick Start

## Openikt Server

#### 1 - Environment Preparation

> Ubuntu 20.04 default install python3.8. if you didn't have, please visit: https://www.python.org/ install.

	Recommended to use a virtual environment

```shell
# Install dependency packages
sudo apt install python3-venv

# Generate virtual environment 
python3 -m venv {your virtualenv name} 

# Enter virtual environment 
source ./{your virtualenv name}/bin/activate 

# exit 
Deactivate 
```

#### 2 - Clone Project Code

```shell
# github code
git clone https://github.com/intel/openikt.git
```

#### 3 - **Install Requirement**

```shell
# Enter the directory
cd openikt-server 

# install (in virtual environment)
pip install -r requirements.txt 
```

#### 4 - Database Migration

```shell
python3 manage.py makemigrations 
python3 manage.py migrate 
```

#### 5 - Create Superuser

```python
python3 manage.py createsuperuser 
```

#### 6 - Run Server

###### 	Development Environment

```python
python3 manage.py runserver 0:8000
```

> Visit: http://localhost:8000/admin use your superuser account to login. 

###### 	Production Environment

> Recommended to use uwsgi to managed projects. How to use Django with uWSGI: https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/uwsgi/

```python
# install
python -m pip install uwsgi

# After configuring according to the project uwsgi.ini file
uwsgi --ini uwsgi.ini

# exit
uwsgi --stop uwsgi.pid
```

## Openikt Web

#### 1 - Environment Preparation

> Need node.js, if you didn't have, please visit: https://nodejs.org/ install.

```shell
cd openikt-web

# install package
npm install
```

###### 	Development Environment

```shell
# config openikt server host
vim .env.development 

VUE_APP_DEV_SERVER_PROXY_URL = http://xxx:8000
VUE_APP_AJAX_URL = /v1

# run
npm run serve
```

> Please visit: http://xxx:7777, web page work on.

###### 	Production Environment

```shell
# config openikt server host
vim .env.production

VUE_APP_AJAX_URL = /v1

# build
npm run build
```

## Deploy

> After, can use nginx to proxy your project. https://nginx.org/en/, Please refer to:

```nginx
server {
        listen          443 ssl;
        #server_name    localhost;
        server_name     xxxx;

        ssl_certificate        xxx;
        ssl_certificate_key    xxx;

        location / {
                root .../os.linux.kernel.devops.openikt/openikt-web/dist;
                index index.html index.htm;
                try_files $uri $uri/ @router;
                access_log .../xxx.log;
        }

        location /v1/ {
        	# your openikt server url
            proxy_pass xxx;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            add_header Access-Control-Allow-Methods *;
            add_header Access-Control-Max-Age 3600;
            add_header Access-Control-Allow-Credentials true;
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Headers 'DNT,X-Mx-ReqToken,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
            if ($request_method = OPTIONS ) {
                return 200;
            }
        }
        
         location @router {
                rewrite ^.*$ /index.html last;
        }

        }
```


# Setup with Docker Compose

You can setup all the Openikt services with docker-compose/setup.py,
please refer docker-compose/README.md for more information.



# Document 

Please refer [https://github.com/intel/openikt/wiki](https://github.com/intel/openikt/wiki)



# Contributing

* Issues

Any bug or issue, please submit issues.

* Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.



