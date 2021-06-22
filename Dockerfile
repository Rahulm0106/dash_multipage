# Use python, version 3.6 as the base image.
# We won't install debian packages, so just use the slim variant.
FROM python:3.6

# Install required python packages
# Note: This way of formating the instruction allows to easily
# add/remove/comment packages

RUN mkdir -p /work
WORKDIR /work


COPY requirements.txt /work/requirements.txt



RUN pip install -r requirements.txt





# ADD displaydata.csv  /work/displaydata.csv

ADD index.py  /work/index.py 
ADD wsgi.py /work/wsgi.py
ADD app.py /work/app.py 



### the applications
ADD apps/app1.py /work/apps/app1.py 
ADD apps/app2.py /work/apps/app2.py 
ADD apps/displayAll.py /work/apps/displayAll.py
ADD apps/app3.py /work/apps/app3.py 
ADD apps/app4.py /work/apps/app4.py 
ADD apps/app5.py /work/apps/app5.py 
ADD apps/app6.py /work/apps/app6.py 
ADD apps/app7.py /work/apps/app7.py 
ADD apps/app8.py /work/apps/app8.py
ADD apps/home.py /work/apps/home.py
ADD apps/__init__.py /work/apps/__init__.py  

### the css files and images
ADD static/plotly(8).png /work/static/plotly(8).png
ADD static/plotly(9).png /work/static/plotly(9).png
ADD static/plotly(10).png /work/static/plotly(10).png
ADD static/plotly(12).png /work/static/plotly(12).png
ADD static/custom.css /work/static/custom.css
ADD static/GUI.css /work/static/GUI.css



 
## change it to display.py to run secind script
CMD [ "python", "./index.py" ]


# Declare port 8888
EXPOSE 8050
