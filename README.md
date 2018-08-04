# NextApp
API Connector for Next App

# One installed, All connected
This module is currently using Frappe bench app module, you must have Frappe Environment before to install this module app

## Next Sales v1.2
Please always check for the update of your system when there's warning from the app by using git pull and reload the frappe
```
git pull
sudo supervisorctl reload
```

This API Connector is use by Next Sales Application on Android Google Playstore.
[app link download](https://play.google.com/store/apps/details?id=com.digitalasiasolusindo.nextsales)

You must install this app into your frappe / erpnext using bench
More information about frappe bench [click here](https://github.com/frappe/bench)

### Manual Install using Bench
1. Getting the app from github  
You must run bench on your frappe directory
```
bench get-app nextapp https://github.com/ptdas/NextApp
```

2. Install the app  
You need to install the app into your site
```
bench --site [sitename] install-app nextapp
```
sitename : your existing sitename

3. Reload your bench  
This may take a several seconds to reload your bench  
Run this command in root  
```
sudo supervisorctl reload
```

#### License

PT. Digital Asia Solusindo - Indonesia SalesForce API Connector  
MIT - Frappe | ERPNext
