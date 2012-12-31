#!/bin/bash

echo "Pulling repo."
ssh metatron.pault.ag "cd /srv/www/uwsgi/app/hy; git pull"
ssh -l www metatron.pault.ag "kill-apps; start-apps"
