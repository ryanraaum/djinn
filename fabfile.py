DEPENDENCIES = ['oldowan.mtdna',
                'oldowan.polymorphism',
                'oldowan.fasta',
                'oldowan.mtconvert',
                'PyYAML']

def production():
    'Environment settings for deployment to webfaction host.'
    config.fab_hosts = ['mtdnaresource.com']
    config.dist_root = "webapps/django/dists"
    config.dist_name = "dist_$(fab_timestamp)"
    config.dist_dest = "%s/%s" % (config.dist_root, config.dist_name)
    config.deploy_dir = "webapps/django/djinn"
    config.start_bin = "webapps/django/apache2/bin/start"
    config.stop_bin = "webapps/django/apache2/bin/stop"
    config.restart_bin = "webapps/django/apache2/bin/restart"
    config.easy_install = "PYTHONPATH=$HOME/webapps/django/lib/python2.5/:$HOME/webapps/django/ easy_install-2.5 --always-unzip --install-dir=$HOME/webapps/django/lib/python2.5/ --script-dir=$HOME/bin"
    config.python = "PYTHONPATH=$HOME/webapps/django/lib/python2.5/:$HOME/webapps/django/ python2.5"

def restart_webserver():
    'Restart webserver.'
    run("$(restart_bin)")

def start_webserver():
    'Start webserver.'
    run("$(start_bin)")

def stop_webserver():
    'Stop webserver.'
    run("$(stop_bin)")

def deploy_production_settings():
    'Deploy the production private_settings file'
    # the 'touch' is a hack to work around a fabric bug
    # (i.e. target file has to exist to be copied over...)
    run("touch webapps/django/private_settings.py")
    put("production_settings.py", "webapps/django/private_settings.py")

def create_dist():
    'Create a zip of the distribution files.'
    # include all .py source files
    local("zip -r dist . -i \*.py")
    # but remove the private_settings.py and production_settings.py files
    local("zip -d dist *_settings.py")
    # also remove this fabfile from the distribution
    local("zip -d dist fabfile.py")
    # include all html files
    local("zip -r dist . -i \*.html")
    # include everything under static
    local("zip -r dist . -i static/\*")
    # include the depends.txt file (is this needed?)
    local("zip -r dist . -i depends.txt")

def upload_dist():
    'Upload local distribution zip to host.'
    # make the directory that the distribution will be unzipped into
    run("mkdir -p $(dist_dest)")
    # move the local distribution (dist.zip) to the host
    run("touch $(dist_root)/dist.zip")
    put("dist.zip", "$(dist_root)/dist.zip")
    # unzip it into the destination directory created earlier
    run("unzip $(dist_root)/dist.zip -d $(dist_dest)")
    # link the production private settings into the app
    run("ln -s ../../private_settings.py $(dist_dest)/private_settings.py")
    # get rid of the distribution zip
    run("rm $(dist_root)/dist.zip")

def enable_dist():
    'Link latest uploaded distribution into the deploy directory'
    run("rm -f $(deploy_dir)")
    run("ln -s dists/`ls -r $(dist_root) | sed -n '1p'` $(deploy_dir)")

def deploy():
    'Make a distribution from the current state of the app and deploy it'
    create_dist()
    upload_dist()
    enable_dist()

def install_dependencies():
    'Install dependencies using easy_install.'
    for dep in DEPENDENCIES:
        run("$(easy_install) %s" % dep)

def upgrade_dependencies():
    'Upgrade dependencies using easy_install.'
    for dep in DEPENDENCIES:
        run("$(easy_install) -U %s" % dep)

