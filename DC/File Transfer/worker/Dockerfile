FROM altariax0x01/genworker

WORKDIR /app

COPY . /app
#RUN apk update && apk add make automake gcc g++ subversion python3-dev python-dev python3 py-pip nfs-utils && pip3 install --trusted-host pypi.python.org -r requirements.txt
#RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
#RUN chmod +x ./start.sh
#RUN apt-get -y install ssh rsync
EXPOSE 4000 5000 873 22

ENV NAME ApatheticML

#ENTRYPOINT [ "start.sh" ]
