# Kubernetes ELB Security

This is a Kubernetes controller that creates AWS security group rules for service ELB like ingress-nginx with granding access from all kubernetes nodes

It is useful if your services with Type `LoadBalancer` having firewall restrictions.


## InCluster
`/kube-elb-security -alsologtostderr`
 
 In that case all required information would be taken from AWS instance metadata
 
 
 #### Note
 Pod needs to be running on master node due to AWS InstanceProfile permissions
 
 
 ## Local
 `docker build --tag kube-elb-security .`
 
 `docker run -it --rm kube-elb-security /kube-elb-security -logtostderr -inCluster=false -region=us-east-1 -vpc-id=vpc-01234567`
 
 
 ## Services filter
 By default controller watches on services with label `app=ingress-nginx`
 Could be defined by flag `-labelSelector=app=myapp`
