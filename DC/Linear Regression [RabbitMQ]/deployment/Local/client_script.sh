#!/bin/bash
echo "Distribution Engine Client System"
echo "Performing Magic"
header=0
while [ "$1" != "" ]; do
    case $1 in
        -f | --file )           shift
                                filename=$1
                                ;;
        -c | --path )           shift
                                program_path=$1
                                ;;
        -z | --hdfs )           hdfs=1
                                ;;
        -r | --remove-headers ) header=1
                                ;;
        #-h | --help )           usage
        #                        exit
        #                        ;;
        #* )                     usage
        #                        exit 1
    esac
    shift
done
##creation of the master and waiting goes here
read -p "Enter K8s Controller External IP : " controller_ip

read -p "Enter split number : " split_number
controlpod="$(kubectl get pods -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector 'target=controller')"
echo $controlpod
masterpod="$(kubectl get pods -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' --selector 'target=master')"
echo $masterpod
rsync -av --progress --stats -e './rsync_assist.sh' $filename "$controlpod:/mnt/shadow/"
rsync -av --progress --stats -e './rsync_assist.sh' $filename "$masterpod:/app/"
#echo curl -d "'""$(generate_post_data)""'" -H \"Content-Type:application/json\" -X POST "http://$controller_ip:4000/api/startdeploy"
#echo "$(curl -d $(generate_post_data) -H \"Content-Type:application/json\" -X POST "http://$controller_ip:4000/api/startdeploy")"

python3 req.py "$controller_ip"':4000' "api/startdeploy" "$filename" "$split_number" "$program_path" "$header" "$split_number"
