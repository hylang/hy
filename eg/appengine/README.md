App Engine skeleton for hylang
==============================

# Demo

[proppy-hy.appspot.com](https://proppy-hy.appspot.com)
[proppy-hy.appspot.com/paultag](https://proppy-hy.appspot.com/paultag)


# Setup
```
pip install -r requirements.txt -t env
```

# Run locally
```
dev_appserver.py .
```

# Deploy
```
appcfg.py -a ${APPID} --oauth2 update .
```
