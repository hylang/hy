import shutil
from distutils.sysconfig import get_python_lib

python_lib = get_python_lib()
shutil.copy('hy.pth', python_lib)
