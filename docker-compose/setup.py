#!/usr/bin/env python3

import sys
import re
import os
import argparse
import subprocess
import importlib
import time


def main():
    # copy environs to default
    default_http_proxy = os.environ.get('http_proxy', os.environ.get('HTTP_PROXY', ''))
    default_https_proxy = os.environ.get('https_proxy', os.environ.get('HTTPS_PROXY', ''))
    default_socks_proxy = os.environ.get('socks_proxy', 
                                         os.environ.get('SOCKS_PROXY',
                                                         os.environ.get('all_proxy',
                                                                        os.environ.get('ALL_PROXY', '')
                                                                        )
                                                         )
                                         )
    default_no_proxy = os.environ.get('no_proxy', os.environ.get('NO_PROXY', ''))

    # Create the top-level parser
    parser = argparse.ArgumentParser(description='The command tool to set up, update or remove OpenIKT service.')
    
    # Add sub-command parsers
    subparsers = parser.add_subparsers(dest='command', required=True, help='sub-command help', 
                                       title='subcommands', metavar='<subcommand>')
    
    # install sub-command
    parser_install = subparsers.add_parser('install', help='install command help')
    parser_install.add_argument('--port', type=str, default='80',
                                help='the port on the host mapping to openikt-web container')
    parser_install.add_argument('--data-dir', type=str, default='/app/postgres',
                                help='volume mapping data directory for postgres on host')
    parser_install.add_argument('--db-password', type=str, default='mypass',
                                help='password for postgres')
    parser_install.add_argument('--server-log-dir', type=str, default='/app/logs/server',
                                help='openikt-server log directory on the host mapping to container')
    parser_install.add_argument('--web-log-dir', type=str, default='/app/logs/web',
                                help='openikt-web log directory on the host mapping to container')

    parser_install.add_argument('--enable-https', action='store_true', default=False,
                                help='enable https and --cert, --cert-key is required')
    parser_install.add_argument('--https-port', type=int, default=443,
                                help='specify your https port, the default is 443')
    parser_install.add_argument('--cert', type=str, default='ssl/server.crt',
                                help='specify cert file name in ssl directory (put the cert in the ssl directory)')
    parser_install.add_argument('--cert-key', type=str, default='ssl/server.key',
                                help='specify cert private key file name in ssl directory (also put the cert key file in the ssl directory)')
    parser_install.add_argument('--nginx-servername', type=str, action='store',
                                help='specify the nginx server_name (required if --enable-https is enabled)')

    parser_install.add_argument('--http-proxy', type=str,
                                help='http proxy in the format http://<myproxy:port>',
                                default=default_http_proxy, required=False)
    parser_install.add_argument('--https-proxy', type=str,
                                help='https proxy in the format http://<myproxy:port>',
                                default=default_https_proxy, required=False)
    parser_install.add_argument('--socks-proxy', type=str,
                                help='socks proxy in the format socks://myproxy:port>', 
                                default=default_socks_proxy, required=False)
    parser_install.add_argument('--no-proxy', type=str,
                                help='comma-separated list of hosts that should not be connected to via the proxy',
                                default=default_no_proxy, required=False)

    parser_install.set_defaults(func=install)
    
    # uninstall sub-command
    parser_uninstall = subparsers.add_parser('uninstall',
                                             help='uninstall remove all services and remove all data in database')
    parser_uninstall.add_argument('--remove-data', action='store_true', default=False, 
                                  help='remove database data and application logs')
    parser_uninstall.set_defaults(func=uninstall)
    
    # update sub-command
    parser_update = subparsers.add_parser('update', help='update one or all services')

    group = parser_update.add_mutually_exclusive_group(required=True)
    group.add_argument('--service', type=str, help='service name for update')
    group.add_argument('--all', action='store_true', help='update all services')
    parser_update.set_defaults(func=update)
    
    # Parse command-line arguments
    args = parser.parse_args()

    # Execute the corresponding action based on the sub-command
    args.func(args)
    
def install(args):
    if args.enable_https and args.nginx_servername is None:
        print("--enable-https requires --nginx-servername to be specified.")
        sys.exit(2)

    # check if project docker-compose exist
    command = 'docker compose ls -a | grep "^docker-compose"'
    return_code = subprocess.call(command, shell=True)
    if return_code == 0:
        print("openikt compose project exist, please run ./setup.py uninstall first!")
        sys.exit(1)

    if args.enable_https:
        if not os.path.isfile(args.cert) or not os.path.isfile(args.cert_key):
            print(f'you enabled https, but {args.cert} or {args.cert_key} is not exist')
            sys.exit(2)

    if not os.path.exists(args.data_dir) or not os.path.exists(args.server_log_dir) or not os.path.exists(args.web_log_dir):
        print(f'local directory {args.data_dir} or {args.server_log_dir} or {args.web_log_dir} is not exist')
        sys.exit(2)

    # Perform reqirement checks
    check_requirements()

    # all check finished

    custom_env = os.environ.copy()
    custom_env["http_proxy"] = args.http_proxy
    custom_env["https_proxy"] = args.https_proxy
    custom_env["socks_proxy"] = args.socks_proxy
    custom_env["no_proxy"] = args.no_proxy

    # create compose.yml
    template_file = 'compose.yml.j2'
    output_file = 'compose.yml'
    context = {
        'db_data_dir' : args.data_dir,
        'password' : args.db_password,
        'port' : args.port,
        'server_log_dir' : args.server_log_dir,
        'web_log_dir' : args.web_log_dir,
        'http_proxy' : args.http_proxy,
        'https_proxy' : args.https_proxy,
        'socks_proxy' : args.socks_proxy,
        'no_proxy' : args.no_proxy,
        'enable_https': args.enable_https,
        'https_port' : args.https_port
    }
    render_template(template_file, output_file, context)

    # create nginx-web.conf
    template_file = 'nginx-web.conf.j2'
    output_file = 'nginx-web.conf'
    context = {
        'enable_https': args.enable_https,
        'cert': args.cert,
        'cert_key': args.cert_key,
        'nginx_servername': args.nginx_servername
    }
    render_template(template_file, output_file, context)

    # npm build
    script_path = os.path.abspath(__file__)
    script_directory = os.path.dirname(script_path)
    print('npm building, it may take a few minutes ...')
    command = ('docker run --rm -v %s/../openikt-web:/opt/openikt-web -e http_proxy -e https_proxy -e socks_proxy '
                          '-e no_proxy public.ecr.aws/docker/library/node:18.19.1 ' 
                          'bash -c "cd /opt/openikt-web;npm install && VUE_APP_AJAX_URL=/v1/ npm run build"' % script_directory
    )
    return_code = subprocess.call(command, shell=True, env=custom_env)
    if return_code != 0:
        print("npm build failed!")
        sys.exit(1)

    # docker compose build and get all services up
    custom_env['COMPOSE_PROJECT_NAME'] = 'docker-compose'
    return_code = subprocess.call(['docker', 'compose', 'up', '--build', '-d'], shell=False, env=custom_env)
    if return_code != 0:
        print('docker compose up failed!')
        sys.exit(1)

    # Apply any pending migrations / initialize the database.
    return_code = subprocess.call(['docker', 'compose', 'exec', '-T', 'openikt-server', 
                                   'python3', '/opt/openikt-server/manage.py', 'makemigrations'], shell=False)
    if return_code != 0:
        print('make migrations failed!')
        sys.exit(1)
    else:
        print('make migrations sucess and wait for postgres ready ...')
        time.sleep(10)
    return_code = subprocess.call(['docker', 'compose', 'exec', '-T', 'openikt-server', 
                                   'python3', '/opt/openikt-server/manage.py', 'migrate'], shell=False)
    if return_code != 0:
        print('applying migrations failed!')
        sys.exit(1)

def uninstall(args):
    if args.remove_data:
        print("""
        WARNING: continuing will wipe out any existing data in the database, application logs, and
                 uninstall the application. Press Ctrl+C now if this is not what you want.
        """)
    else:
        print("""
        WARNING: continuing will uninstall the application, and the data in database, application
                 logs will be retained on host. Press Ctrl+C now if this is not what you want.
        """)
    try:
        promptstr = 'Press Enter to begin uninstallation (or Ctrl+C to exit)...'
        input(promptstr)
    except KeyboardInterrupt:
        print('exit')
        sys.exit(2)

    print('Uninstalling...')
    if args.remove_data:
        return_code = subprocess.call(['docker', 'compose', 'run', '--rm', 'openikt-web',
                                       'sh', '-c', 'rm -rf /opt/logs/*'], shell=False)
        if return_code != 0:
            print('remove openikt-web logs failed!')
            sys.exit(1)

        return_code = subprocess.call(['docker', 'compose', 'run', '--rm', 'openikt-server',
                                       'sh', '-c', 'rm -rf /opt/logs/*'], shell=False)
        if return_code != 0:
            print('remove openikt-server logs failed!')
            sys.exit(1)

        return_code = subprocess.call(['docker', 'compose', 'run', '--rm', 'openikt-db', 'sh', '-c', 'rm -rf /var/lib/postgresql/data/*'], shell=False)
        if return_code != 0:
            print('remove database data failed!')
            sys.exit(1)

    return_code = subprocess.call(['docker', 'compose', 'down'], shell=False)
    if return_code != 0:
        print('docker compose down failed!')
        sys.exit(1)

    print('Uninstall completly!')

def update(args):
    if args.service:
        return_code = subprocess.call(['docker', 'compose', 'up', f'{args.service}', '--build', '-d'], shell=False)
    else:
        return_code = subprocess.call(['docker', 'compose', 'up', '--build', '-d'], shell=False)

    if return_code != 0:
        print('Update service failed!')
        sys.exit(1)
    print('Update service sucess!')

def check_requirements():
    """Check if Python3, jinja2 module, and Docker meet the requirements."""
    # Check if Python 3 command exists
    try:
        subprocess.check_output([sys.executable, "--version"], stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print('Python3 was not found. Please ensure Python3 is installed and in your PATH.')
        sys.exit(1)

    # Check if the jinja2 module is installed
    try:
        importlib.import_module('jinja2')
    except ImportError:
        print('The required module jinja2 is not found and begin to install ...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'jinja2'])
        print('The required module jinja2 installed.')

    # Check if the Docker version meets the requirement
    try:
        output = subprocess.check_output(['docker', '--version'], universal_newlines=True)
        version_match = re.search(r'(\d+\.\d+)', output)
        if version_match:
            docker_version = version_match.group(1)
            if tuple(map(int, docker_version.split('.'))) < (20, 10):
                print(f'Docker version is lower than 20.10. Your version: {docker_version}')
                sys.exit(1)
    except FileNotFoundError:
        print('Docker command not found. Please ensure Docker is installed and in your PATH.')
        sys.exit(1)

    # If all checks pass, the rest of the script can proceed
    print('All checks passed. Script can proceed.')

def render_template(template_file, output_file, context):
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_file)
    
    rendered_content = template.render(context)
    
    with open(output_file, 'w') as f:
        f.write(rendered_content)
    
    print(f'Template rendered and saved to {output_file}')

if __name__ == '__main__':
    main()
