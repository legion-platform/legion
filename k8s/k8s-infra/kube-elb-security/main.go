package main

import (
	"flag"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/credentials/ec2rolecreds"
	"github.com/aws/aws-sdk-go/aws/ec2metadata"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/ec2"
	"github.com/golang/glog"
	"k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/labels"
	"k8s.io/apimachinery/pkg/watch"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type sgRule struct {
	name     string
	publicIP string
}

type port struct {
	number   int64
	protocol string
}

type sgRules struct {
	ports []port
	sgID  string
	rules []sgRule
}

var sess *session.Session
var vpcID *string
var region *string
var clientset *kubernetes.Clientset
var labelSelector *string
var servicesWatcher watch.Interface
var clusterName string

func init() {
	var err error

	labelSelector = flag.String("labelSelector", "app=ingress-nginx", "key=value pair for services filter")

	inCluster := flag.Bool("inCluster", true, "Use Kubernetes inCLuster connection")
	vpcID = flag.String("vpc-id", "", "Define AWS vpc-id only if inCluster=false")
	region = flag.String("region", "", "Define AWS region only if inCluster=false")

	var kubeconfig *string
	if home := homeDir(); home != "" {
		kubeconfig = flag.String("kubeconfig", filepath.Join(home, ".kube", "config"), "(optional) absolute path to the kubeconfig file")
	} else {
		kubeconfig = flag.String("kubeconfig", "", "absolute path to the kubeconfig file")
	}

	flag.Parse()

	metadata := ec2metadata.New(session.New())

	if *inCluster {
		config, err := rest.InClusterConfig()
		if err != nil {
			glog.Fatal(err.Error())
		}
		clientset, err = kubernetes.NewForConfig(config)
	} else {
		config, err := clientcmd.BuildConfigFromFlags("", *kubeconfig)
		if err != nil {
			glog.Fatal(err.Error())
		}
		clientset, err = kubernetes.NewForConfig(config)
	}

	if *region == "" {
		if *inCluster {
			*region, err = metadata.Region()
			if err != nil {
				glog.Fatal("Unable to retrieve the region from the EC2 instance %v\n", err)
			}
		} else {
			glog.Fatal("AWS region is not defined. Flag example: -region us-east1")
		}
	}

	if *vpcID == "" {
		if *inCluster {
			networkMac, err := metadata.GetMetadata("network/interfaces/macs/")
			if err != nil {
				glog.Fatalf("Unable to retrieve EC2 instance network interface mac address %v\n", err)
			}
			*vpcID, err = metadata.GetMetadata("network/interfaces/macs/" + networkMac + "/vpc-id")
			if err != nil {
				glog.Fatalf("Unable to retrieve EC2 instance VPC-ID %v\n", err)
			}
		} else {
			glog.Fatalf("AWS vpc-id is not defined. Flag example: -vpc-id=vpc-01234567")
		}
	}

	creds := credentials.NewChainCredentials(
		[]credentials.Provider{
			&credentials.EnvProvider{},
			&credentials.SharedCredentialsProvider{},
			&ec2rolecreds.EC2RoleProvider{Client: metadata},
		})

	sess, err = session.NewSession(&aws.Config{
		Credentials: creds,
		Region:      aws.String(*region)},
	)

	if err != nil {
		glog.Fatal(err.Error())
	}

	clusterName = getClusterName()

}

func main() {

	glog.Info("Starting Nodes watcher")

	nodesWatcher, err := clientset.CoreV1().Nodes().Watch(metav1.ListOptions{})

	if err != nil {
		glog.Fatal(err.Error())
	}

	resultChan := nodesWatcher.ResultChan()

	for event := range resultChan {
		node, ok := event.Object.(*v1.Node)
		if !ok {
			glog.Fatal("Unexpected type")
		}
		switch event.Type {
		case watch.Added:
			glog.Infof("Added new Kubernetes node %v", node.Name)
			go func() { restartServiceWatcher() }()
		case watch.Deleted:
			glog.Infof("Kubernetes node %v was deleted", node.Name)
			//TODO implement rule clean-up
		}
	}
}

func restartServiceWatcher() {
	if servicesWatcher != nil {
		glog.Infof("Starting k8s client watcher on services using labels %v", *labelSelector)
		servicesWatcher.Stop()
	}
	startServiceWatcher()
}

func startServiceWatcher() {

	l, err := labels.Parse(*labelSelector)
	if err != nil {
		glog.Fatalf("Failed to parse selector %q: %v", *labelSelector, err)
	}

	serviceListOptions := metav1.ListOptions{
		LabelSelector: l.String(),
	}

	servicesWatcher, err = clientset.CoreV1().Services(v1.NamespaceAll).Watch(serviceListOptions)
	if err != nil {
		glog.Fatal(err.Error())
	}

	time.Sleep(time.Second) //Sync channels

	rules := getNodesPublicAddresses()

	for _, rule := range getPublicEIPs() {
		rules = append(rules, rule)
	}

	resultChan := servicesWatcher.ResultChan()

	for event := range resultChan {
		svc, ok := event.Object.(*v1.Service)
		if !ok {
			glog.Fatal("Unexpected type")
		}
		switch event.Type {
		case watch.Added:
			processService(svc, rules)
		case watch.Modified:
			processService(svc, rules)
		case watch.Deleted:
			glog.Infof("Processing deleted service %v", svc.Name)
			//TODO Implement cleanup after service deletion
		}
	}
}

func processService(service *v1.Service, nodes []sgRule) {

	if len(service.Status.LoadBalancer.Ingress) == 0 {
		glog.Infof("Service %v doesn't have any ELB endpoints", service.Name)
	}

	var rules []sgRules
	var elbNames []string
	for _, name := range service.Status.LoadBalancer.Ingress {
		glog.Infof("Processing service %v ELB (%v)", service.Name, name)
		elbNames = append(elbNames, name.Hostname)
	}
	var elbPorts []port
	for _, elbStatusPorts := range service.Spec.Ports {
		elbPorts = append(elbPorts, port{
			number:   int64(elbStatusPorts.Port),
			protocol: strings.ToLower(string(elbStatusPorts.Protocol)),
		})
	}
	for _, sg := range getSG(elbNames) {
		rules = append(rules, sgRules{
			ports: elbPorts,
			sgID:  sg,
			rules: nodes,
		})
	}

	updateSGs(rules)
}

func getNodesPublicAddresses() (ret []sgRule) {

	nodes, err := clientset.CoreV1().Nodes().List(metav1.ListOptions{})

	if err != nil {
		panic(err.Error())
	}

	for _, node := range nodes.Items {
		for _, addr := range node.Status.Addresses {
			if addr.Type == "ExternalIP" {
				ret = append(ret, sgRule{
					name:     node.Name,
					publicIP: addr.Address + "/32",
				})
			}
		}
	}
	return
}

func getPublicEIPs() (ret []sgRule) {
	svc := ec2.New(sess)

	eips, err := svc.DescribeAddresses(&ec2.DescribeAddressesInput{
		Filters: []*ec2.Filter{
			{
				Name:   aws.String("tag:KubernetesCluster"),
				Values: []*string{aws.String(clusterName)},
			},
		},
	})

	if err != nil {
		glog.Warning(err.Error())
	}

	for _, eip := range eips.Addresses {
		ret = append(ret, sgRule{
			name:     *eip.AllocationId,
			publicIP: *eip.PublicIp + "/32",
		})
	}

	return ret

}

func getClusterName() (tag string) {

	node, err := clientset.CoreV1().Nodes().List(metav1.ListOptions{
		LabelSelector: "kubernetes.io/role=master",
		Limit:         1,
	})

	if err != nil {
		glog.Fatal(err.Error())
	}

	if len(node.Items) == 0 {
		glog.Fatal("Found 0 master nodes")
	}

	masterPrivateIP := ""

	for _, address := range node.Items[0].Status.Addresses {
		if address.Type == "InternalIP" {
			masterPrivateIP = address.Address
		}
	}

	if masterPrivateIP == "" {
		glog.Fatal("Failed to get masters " + node.Items[0].Name + " InternalIP")
	}

	svc := ec2.New(sess)
	instances, err := svc.DescribeInstances(&ec2.DescribeInstancesInput{
		Filters: []*ec2.Filter{
			{
				Name:   aws.String("private-ip-address"),
				Values: []*string{aws.String(masterPrivateIP)},
			},
		},
	})

	if err != nil {
		glog.Fatal(err.Error())
	}

	if len(instances.Reservations) == 0 {
		glog.Fatal("AWS returned 0 reservations for master instance " + node.Items[0].Name + "\n" + instances.String())
	}

	if len(instances.Reservations[0].Instances) == 0 {
		glog.Fatal("AWS returned 0 instances for master instance " + node.Items[0].Name + "\n" + instances.String())
	}

	for _, instanceTag := range instances.Reservations[0].Instances[0].Tags {
		if *instanceTag.Key == "KubernetesCluster" {
			tag = *instanceTag.Value
		}
	}

	return
}

func getSG(elbURLs []string) (ret []string) {
	var groupNames []string
	for _, name := range elbURLs {
		groupNames = append(groupNames, "k8s-elb-"+strings.Split(name, "-")[0])
	}

	svc := ec2.New(sess)

	result, err := svc.DescribeSecurityGroups(&ec2.DescribeSecurityGroupsInput{
		GroupIds: nil,
		Filters: []*ec2.Filter{
			{
				Name: aws.String("vpc-id"),
				Values: []*string{
					aws.String(*vpcID),
				},
			},
		},
	})

	if err != nil {
		glog.Fatal(err.Error())
	}

	if len(result.SecurityGroups) == 0 {
		glog.Fatalf("Failed to get security groups at VPC %v", *vpcID)
	}

	for _, sg := range result.SecurityGroups {
		for _, group := range groupNames {
			if *sg.GroupName == group {
				ret = append(ret, *sg.GroupId)
			}
		}
	}
	return
}

func updateSGs(rules []sgRules) {
	svc := ec2.New(sess)

	for _, rule := range rules {

		existingRules, err := svc.DescribeSecurityGroups(&ec2.DescribeSecurityGroupsInput{
			GroupIds: []*string{&rule.sgID},
		})

		if err != nil {
			glog.Fatal(err.Error())
		}

		var permissions []*ec2.IpPermission

		for _, record := range rule.rules {
			for _, port := range rule.ports {
				applyRule := true
				for _, sg := range existingRules.SecurityGroups {
					for _, existingRule := range sg.IpPermissions {
						for _, ipRange := range existingRule.IpRanges {
							if (*existingRule.FromPort == port.number) &&
								(strings.ToLower(*existingRule.IpProtocol) == strings.ToLower(port.protocol)) &&
								(*ipRange.CidrIp == record.publicIP) {
								glog.Infof("Rule at %v for CidrIP %v port %v protocol %v already exists", rule.sgID, *ipRange.CidrIp, *existingRule.FromPort, *existingRule.IpProtocol)
								applyRule = false
							}
						}
					}
				}
				if applyRule {
					permissions = append(permissions, &ec2.IpPermission{
						IpProtocol: aws.String(port.protocol),
						FromPort:   aws.Int64(port.number),
						ToPort:     aws.Int64(port.number),
						IpRanges: []*ec2.IpRange{
							{CidrIp: aws.String(record.publicIP),
								Description: aws.String("Rule for k8s " + record.name + " Port " + strconv.FormatInt(port.number, 10))},
						},
					})
				}
			}
		}

		if len(permissions) > 0 {

			for _, permission := range permissions {
				glog.Infof("Applying rule at %v for CidrIP %v port %v protocol %v",
					rule.sgID,
					*permission.IpRanges[0].CidrIp,
					*permission.FromPort,
					*permission.IpProtocol)
			}

			_, err = svc.AuthorizeSecurityGroupIngress(&ec2.AuthorizeSecurityGroupIngressInput{
				GroupId:       &rule.sgID,
				IpPermissions: permissions,
			})

			if err != nil {
				glog.Fatal(err.Error())
			}

		} else {
			glog.Infof("%v: No new rules to apply", rule.sgID)
		}
	}
}

func homeDir() string {
	if h := os.Getenv("HOME"); h != "" {
		return h
	}
	return os.Getenv("USERPROFILE") // windows
}
