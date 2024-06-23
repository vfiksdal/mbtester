import PyInstaller.__main__
import shutil
from common import *

print('Deleting old build environment')
try:
    shutil.rmtree('build')
except:
    pass
try:
    shutil.rmtree('dist')
except:
    pass

print('Building v'+Utils.getAppVersion())
PyInstaller.__main__.run(['mbtserver.py','--onefile','--noconsole','--name','mbtserver_gui'])
PyInstaller.__main__.run(['mbtclient.py','--onefile','--noconsole','--name','mbtclient_gui'])
PyInstaller.__main__.run(['mbserver.py','--onefile','--name','mbtserver_cli'])
PyInstaller.__main__.run(['mbclient.py','--onefile','--name','mbtclient_cli'])

print('Copying accompanying files')
shutil.copy('Test_Endian.json','dist')
shutil.copy('Test_Malformed.json','dist')
shutil.copy('Test_Simple.json','dist')
shutil.copy('README.md','dist')
shutil.copy('LICENSE','dist')

print('Archiving output files')
shutil.make_archive('mbtester-'+Utils.getAppVersion(), 'zip', 'dist')

print('Making installer')
nsispath = os.environ.get("PROGRAMFILES(X86)")+'\\NSIS\\makensis.exe'
if os.path.exists(nsispath):
    shutil.copy('extras\\mbtester.nsi','dist')
    os.system('"'+nsispath+'"'+' /NOCD dist\\mbtester.nsi')
    shutil.move('mbtester.exe','mbtester-'+Utils.getAppVersion()+'.exe')
else:
    print('Could not find NSIS -- Skipping')
print('Done!')
