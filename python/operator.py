import python.ec2_config as ec2_config
from python.ssh_client import SSHClient
from kubernetes import client, config
import python.helper as helper
import boto3

class OperatorEc2(ec2_config.Ec2Config):
    def __init__(self, key_id='', secret_id='', region="us-east-1", instance_name=''):
        super().__init__(key_id, secret_id, region, instance_name)
        self.terraform_file_location = ''
        self.ansible_playbook_location = ''
        self.k8_website = ''
        
    def deploy_terraform_ansible (self):
        helper._display_message("Deploying Terraform and Ansible")
        self.get_aws_keys()
        
        install_script = f"""
        sudo yum update
        sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
        sudo yum -y install terraform
        sudo yum install python3
        sudo yum install python3-pip -y
        pip install ansible
        pip install kubernetes
        sudo yum install git -y
        if [ ! -d "madzumo" ]; then
            git clone https://github.com/madzumo/devOps_pipeline.git madzumo
        else
            echo "madzumo folder already exists."
        fi
        aws configure set aws_access_key_id {self.key_id}
        aws configure set aws_secret_access_key {self.secret_id}
        aws configure set default.region {self.region}
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
        """
        # print(f"What we have\n{self.ec2_instance_public_ip}\n{self.ssh_username}\n{self.ssh_key_path}")
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
        
    def terraform_eks_cluster_up(self):
        helper._display_message("Initialize Terraform")
        install_script = """
        terraform -chdir=madzumo/terraform/aws init
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
        
        helper._display_message("Apply Terraform script\nWaiting on cluster(10 min) Please Wait!")
        install_script = """
        terraform -chdir=madzumo/terraform/aws apply -auto-approve
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
        
        
    def ansible_play_ecommerce(self):
        helper._display_message("Running Ansible Playbook on EKS Cluster")
        install_script =f"""
        ansible-galaxy collection install community.kubernetes
        aws eks --region {self.region} update-kubeconfig --name madzumo-ops-cluster
        ansible-playbook madzumo/ansible/deploy-web.yaml
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
    
    def get_k8_service_hostname(self):
        helper._display_message('Get FrondEnd Hostname')
        # ***ONLY WORKS AFTER AWS KUBECONFIG SETUP ON LOCAL****
        config.load_kube_config()
        v1 = client.CoreV1Api()
        namespace = "madzumo-ops"  # Adjust as needed
        service_name = "frontend"  # Replace with your service's name

        try:
            # Query the service by name
            service = v1.read_namespaced_service(name=service_name, namespace=namespace)
            print(f"Service {service_name} details:")
            print(f"UID: {service.metadata.uid}")
            print(f"Service Type: {service.spec.type}")
            print(f"Cluster IP: {service.spec.cluster_ip}")
            
            service_address = service.spec.cluster_ip
            if service_address is None:
                service_address = service.spec.external_ip
            if service_address is None:
                service_address = service.spec.load_balancer_ip
            if service_address is None:
                service_address = service.spec.external_name
            print(f"{service_address}")
            
        except client.exceptions.ApiException as e:
            print(f"An error occurred: {e}")
    
    def output_review(self):
        helper._display_message("Output Review")
        install_script ="""
        kubectl get svc frontend -o=jsonpath='{.status.loadBalancer.ingress[0].hostname}' -n madzumo-ops
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
        self.k8_website = f"http://{ssh_run.command_output}"
        # print(self.k8_website)
        ""
        
    def terraform_eks_cluster_down(self):
        helper._display_message("Removing e-commerce site from EKS Cluster")
        install_script = """
        ansible-playbook madzumo/ansible/remove-web.yaml
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)
        
        helper._display_message("Removing EKS Cluster & other resources (10 min)")
        install_script = """
        terraform -chdir=madzumo/terraform/aws destroy -auto-approve
        """
        ssh_run = SSHClient(self.ec2_instance_public_ip,self.ssh_username,self.ssh_key_path)
        ssh_run.run_command(install_script)

        helper._display_message("All resources for madzumo-ops cluster removed")
    
    def configure_kubernetes_client(self):
        helper._display_message('Config K8s client')
        eks = boto3.client('eks')
        
        # Retrieve cluster information
        cluster_info = eks.describe_cluster(name='madzumo-ops-cluster')['cluster']
        api_server_url = cluster_info['endpoint']
        certificate_authority_data = cluster_info['certificateAuthority']['data']
        
        # Configure the Kubernetes client
        configuration = client.Configuration()
        configuration.host = api_server_url
        configuration.ssl_ca_cert = certificate_authority_data
        
        # Here, you need to set up the authentication token for Kubernetes.
        # This is a placeholder for where you would add the token.
        configuration.api_key['authorization'] = "Bearer <YOUR_TOKEN_HERE>"
        
        client.Configuration.set_default(configuration)
    