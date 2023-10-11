1. Clone repository locally
2. Open terminal in Your directory 
3. In terminal run: 
- python -m venv env => to create Virtual Environment
- source env/bin/activate => to activate environment
- cd Adrian_Kurowski_PhotoApp/ => to enter application directory
- pip install -r requirements.txt => to install all packages needed to run application
- python manage.py migrate => this creates database needed to run application
- python manage.py loaddata initial.json => it initializes Access Tiers data with required thumbnails settings along with first superuser u:admin p:admin
- python manage.py runserver => to run application locally

Remember to add .env file! with KEY, DEBUG and SECRET_KEY defined

All information about API can be found under http://localhost:8000/rest-api/
APISwagger is available under http://localhost:8000/swagger

HOW TO USE APP:

1. Photo List 
	1. Go to http://localhost:8000/photos/
	- enter credentials
	- expected to see list of uploaded photos
2. Photo Upload 
	1. Go to http://localhost:8000/photos/add
	2. enter required data (name, image) 
	3. Send POST request
	- expected status 200
	- expected response with photo details and thumbnail links generated
	
3. Generate thumbnail links 
	1. Go to http://localhost:8000/photos/generate
	- expected to GET list of already uploaded photos with all thumbnail links according to Access Tier
	
4. Generate thumbnail links with expiration time
	1. Go to http://localhost:8000/photos/generateExpired
	- expected to GET list of already uploaded photos with all thumbnail links according to Access Tier
	- if Access Tier does not allow to generate expiring links user gets "You don't have access to generate expiring links, contact Admin to upgrade access tier"
	
5. Delete photo
	1. Go to localhost:8000/photos/delete/{id} where id is id of photo User wants to remove
	- if photo exists, user gets status 200 and can remove photo by pressing DELETE button and confirming it
	- if photo does not exists user gets status 404
	



