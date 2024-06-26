import sys
import helper_config as hc
from s3_config import S3config
from ec2_config import Ec2Config
from operator_config import OperatorEc2
from status_config import StatusPage
from enum import Enum


class MenuOptions(Enum):
    test_connection = '2'
    set_aws_creds = '1'
    setup_pipeline = '3'
    destroy_pipeline = '4'
    status_page = '5'
    quit_demo = '6'


class StartDemo:
    """main class to orchestrate the full pipeline demo"""

    def __init__(self, slowdown=False):
        hc.display_header()
        hc.console_message(hc.welcome_message, hc.ConsoleColors.title)

        self.operator_instance = OperatorEc2('madzumo-ops')
        self.jenkins_instance = Ec2Config('madzumo-jenkins')
        self.menu = MenuOptions
        self.slowdown = slowdown

    def run_demo(self):
        while True:
            hc.console_message(hc.menu_options, hc.ConsoleColors.menu)
            user_option = input('')
            hc.clear_console()
            if user_option == self.menu.test_connection.value:
                self.operator_instance.check_aws_credentials()
            elif user_option == self.menu.set_aws_creds.value:
                self.operator_instance.set_aws_credentials_envars()
                self.operator_instance.reset_ec2_boto3_objects()
            elif user_option == self.menu.setup_pipeline.value:
                self._setup_the_show()
            elif user_option == self.menu.destroy_pipeline.value:
                self._destroy_the_show()
                hc.clear_console()
                hc.display_outro_message()
            elif user_option == self.menu.status_page.value:
                self._status_of_the_show()
            elif user_option == self.menu.quit_demo.value:
                break
            else:
                hc.console_message(['Error', 'Enter option 1-5'], hc.ConsoleColors.error, total_chars=47)
            hc.end_of_line()

    def _setup_the_show(self):
        if self._confirm_the_show():
            hc.console_message(['Please, Do Not Interrupt This Process'], hc.ConsoleColors.warning, total_chars=0)
            # 1. test AWS connection
            if self.operator_instance.check_aws_credentials():
                if self.slowdown:
                    hc.console_message(["Step 1 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)
                    hc.pause_console()

                # 2. Setup S3 bucket for storage
                s3_temp_bucket_name = f"madzumo-ops-{self.operator_instance.aws_account_number}"
                s3_setup = S3config(s3_temp_bucket_name)
                if s3_setup.check_if_bucket_exists():
                    hc.console_message(['Temp S3 bucket exists'], hc.ConsoleColors.info)
                else:
                    hc.console_message(['Creating temp S3 bucket'], hc.ConsoleColors.info)
                    s3_setup.create_bucket()
                self.operator_instance.s3_temp_bucket = s3_temp_bucket_name

                if self.slowdown:
                    hc.console_message(["Step 2 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)

                # 3. Initialize Operator Node Instance (Terraform & Ansible control node)
                hc.console_message(['Creating Operator Node'], hc.ConsoleColors.info)
                self.operator_instance.create_ec2_instance(True)

                if self.slowdown:
                    hc.console_message(["Step 3 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)

                # 4. Install Terraform & Ansible on Operator Node
                self.operator_instance.install_terraform_ansible()

                if self.slowdown:
                    hc.console_message(["Step 4 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)

                # 5. use Terraform to deploy eks cluster
                self.operator_instance.terraform_eks_cluster_up()

                if self.slowdown:
                    hc.console_message(["Step 5 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)

                # 6. use Ansible to apply full e-commerce site on k8s including Prometheus and Grafana
                self.operator_instance.ansible_apply_playbook()

                if self.slowdown:
                    hc.console_message(["Step 6 finish"], hc.ConsoleColors.error, total_chars=0, force_pause=True)

                hc.console_message(['Pipeline Complete!'], hc.ConsoleColors.title)
                hc.pause_console()
                hc.clear_console()
                self._status_of_the_show()

    def _confirm_the_show(self):
        hc.console_message(['This will install the full pipeline ending with a working e-commerce website',
                            'Please do NOT interrupt this process once it begins', 'Proceed? (yes/N)'],
                           hc.ConsoleColors.title)
        response = input('')

        if response.lower() != 'y' and response.lower() != 'yes':
            hc.console_message(['Pipeline Creation Cancelled by User', '(must enter YES)'], hc.ConsoleColors.error, 0)
            return False
        else:
            hc.clear_console()
            return True

    def _destroy_the_show(self):
        # 1. test AWS connection
        if self.operator_instance.check_aws_credentials(False):
            hc.console_message(['REMOVE Pipeline'],hc.ConsoleColors.warning)
            # 2. Populate this workstation with Pipeline data
            self.operator_instance.populate_ec2_instance()

            # 4. Clean up all Objects & remove instances
            self.operator_instance.terraform_eks_cluster_down()
            self.operator_instance.delete_ec2_instance()
            self.operator_instance.remove_local_key_pair()

            # 5. lastly, remove S3 bucket
            hc.console_message(["Terminating temp S3 bucket"], hc.ConsoleColors.info)
            s3_setup = S3config(f"madzumo-ops-{self.operator_instance.aws_account_number}")
            s3_setup.delete_bucket_contents()
            s3_setup.delete_bucket()

    def _status_of_the_show(self):
        if self.operator_instance.check_aws_credentials():
            sp = StatusPage(self.operator_instance)
            sp.populate_status_page(self.operator_instance.populate_ec2_instance(False))


if __name__ == "__main__":
    slowdown = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'slowdown':
            slowdown = True
    start_demo = StartDemo(slowdown=slowdown)
    start_demo.run_demo()
