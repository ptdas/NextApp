# NextApp
API Connector for ERPNext in Next App (Next Sales)

# One installed, All connected
This is a bench app module by Frappe Bench, you must have Frappe Environment before to install this bench app module

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
bench --site [sitename] install-app erpnext
```
sitename : your existing sitename

3. Reload your bench  
This may take a several seconds to reload your bench  
Run this command in root  
```
sudo supervisorctl reload
```

# App Integration
We have already publish our app in Android Playstore and AppStore [Comming Soon]

Here's list of our app :
## Next Sales API v1.2
This app will organize all of your Sales Order, Invoice, Lead, Quotation and Opportunity
Fun way to taking order and mapping your customer to boost your company sales

This API Connector is use by Next Sales Application on Android Google Playstore.
[app link download](https://play.google.com/store/apps/details?id=com.digitalasiasolusindo.nextsales)

Please always check for the update of your system when there's warning from the app by using git pull and reload the frappe
```
git pull
sudo supervisorctl reload
```


#### License

PT. Digital Asia Solusindo - Indonesia SalesForce API Connector  
MIT - Frappe | ERPNext

