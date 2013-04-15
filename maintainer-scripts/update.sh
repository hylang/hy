#!/bin/bash

function metatron {
    ssh metatron.pault.ag $@
}

function www {
    metatron -l www $@
}


metatron "cd /opt/hylang/hy; git pull"
metatron "cd /srv/www/uwsgi/app/shyte; git pull; make"
www "kill-apps"
www "start-apps"
