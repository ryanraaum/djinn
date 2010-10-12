from fabric.api import local
from fabric.api import run
from fabric.api import env
from fabric.api import put
import os
import datetime

def timestamp():
    return(datetime.datetime.utcnow().strftime('%Y_%m_%d_%H-%M-%S'))

DEPENDENCIES = set(line.strip() for line in open('depends.txt', 'rU') 
                   if not line.startswith('[') and len(line.strip()) > 1)

app_name = 'djinn'
env.hosts = ['mtdnaresource.com']
env.user = 'ryanraaum'
base_dir = '/home/ryanraaum'
dist_root = os.path.join(base_dir, "dists", app_name)
dist_name = "dist_%s" % timestamp()
dist_dest = os.path.join(dist_root, dist_name)
deploy_dir = os.path.join(base_dir, 'webapps', app_name, 'myproject')
media_dir = os.path.join('webapps', 'djinn_static')
start_bin = os.path.join(base_dir, 'webapps', app_name, 'apache2', 'bin', 'start')
stop_bin = os.path.join(base_dir, 'webapps', app_name, 'apache2', 'bin', 'stop')
restart_bin = os.path.join(base_dir, 'webapps', app_name, 'apache2', 'bin', 'restart')
easy_install = "PYTHONPATH=$HOME/webapps/%s/lib/python2.6/:$HOME/webapps/%s/ easy_install-2.6 --always-unzip --install-dir=$HOME/webapps/%s/lib/python2.6/ --script-dir=$HOME/bin" % (app_name, app_name, app_name)
python = "PYTHONPATH=$HOME/webapps/%s/lib/python2.6/:$HOME/webapps/%s/ python2.6" % (app_name, app_name)

def restart_webserver():
    'Restart webserver.'
    run(restart_bin)

def start_webserver():
    'Start webserver.'
    run(start_bin)

def stop_webserver():
    'Stop webserver.'
    run(stop_bin)

def rabbit_status():
    'Check rabbitmq status'
    run("rabbitmqctl status")

def rabbit_start():
    'Start rabbitmq'
    run("rabbitmq-server -detached")

def create_db():
    'Create the remote db tables'
    run("%s /home/ryanraaum/webapps/djinn/myproject/manage.py syncdb" % python)

def push_celeryd_init():
    run("mkdir -p /home/ryanraaum/webapps/djinn/celery/bin")
    put("celeryd", "/home/ryanraaum/webapps/djinn/celery/bin/celeryd")
    run("chmod +x /home/ryanraaum/webapps/djinn/celery/bin/celeryd")

def push_media():
    'rsync local media files to server'
    # put local media files up
    local("rsync -Cavuz ./static/ %s@%s:%s" % (env.user, env.host, media_dir))

def create_dist():
    'Create a zip of the distribution files.'
    # include all .py source files
    local("zip -r dist . -i \*.py")
    # also remove this fabfile from the distribution
    local("zip -d dist fabfile.py")
    # include all html files
    local("zip -r dist . -i \*.html")

def upload_dist():
    'Upload local distribution zip to host.'
    # make the directory that the distribution will be unzipped into
    run("mkdir -p %s" % dist_dest)
    # move the local distribution (dist.zip) to the host
    run("touch %s/dist.zip" % dist_root)
    put("dist.zip", "%s/dist.zip" % dist_root)
    # unzip it into the destination directory created earlier
    run("unzip %s/dist.zip -d %s" % (dist_root, dist_dest))
    # get rid of the distribution zip
    run("rm %s/dist.zip" % dist_root)

def enable_dist():
    'Link latest uploaded distribution into the deploy directory'
    run("rm -f %s" % deploy_dir)
    run("ln -s %s/`ls -r %s | sed -n '1p'` %s" % (dist_root, dist_root, deploy_dir))

def deploy():
    'Make a distribution from the current state of the app and deploy it'
    create_dist()
    upload_dist()
    enable_dist()

def install_dependencies():
    'Install dependencies using easy_install.'
    for dep in DEPENDENCIES:
        run("%s %s" % (easy_install, dep))

def upgrade_dependencies():
    'Upgrade dependencies using easy_install.'
    for dep in DEPENDENCIES:
        run("%s -U %s" % (easy_install, dep))

