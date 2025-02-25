kubectl delete service mysql -n europe ;
kubectl delete deployment aki-detection -n europe ;
kubectl delete deployment mysql -n europe ;
kubectl delete pvc aki-detection-state -n europe;

kubectl apply -f mysql-init-sql-configmap.yaml -n europe;
kubectl apply -f coursework4_config.yaml -n europe
