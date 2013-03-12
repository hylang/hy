#!/bin/bash

metatron() {
    ssh metatron.pault.ag $@
}

metatron "cd /srv/www/uwsgi/app/hy; git pull"
metatron "cd /srv/www/uwsgi/app/hy/site; make"
metatron -l www "kill-apps; start-apps"
