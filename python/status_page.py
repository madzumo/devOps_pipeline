from colorama import Back, Fore, Style
import helper_config as hc


class StatusPage:
    def __init__(self, operator):
        self.operator = operator

    def populate_status_page_show(self):
        hc.console_message(['Getting Status'], hc.ConsoleColors.title)
        # AWS status
        aws_conn_title = Back.BLACK + Fore.LIGHTWHITE_EX + Style.BRIGHT + '       AWS Connection:'
        aws_conn_status = Back.BLACK + Fore.LIGHTRED_EX + Style.BRIGHT + 'NO CONNECTION'
        aws_conn_info = ''
        if self.operator.check_aws_credentials(show_result=False):
            aws_conn_status = Back.BLACK + Fore.GREEN + Style.BRIGHT + 'ACTIVE' + Style.NORMAL
            aws_conn_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'              Account: ' + self.aws_account_number + "\n"
            aws_conn_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'               Key ID: ' + self.key_id + "\n"
            aws_conn_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'            Secret ID: ' + self.secret_id

        # Check Pipeline status
        pipeline_title = Back.BLACK + Fore.LIGHTWHITE_EX + Style.BRIGHT + '             Pipeline:'
        pipeline_status = Back.BLACK + Fore.LIGHTRED_EX + Style.BRIGHT + 'NOT SETUP'
        pipeline_info = ''
        # self.download_key_pair() #unablet to download pem file without corruption of data
        if self.operator.get_instance() and self.operator.get_web_url():
            pipeline_status = Back.BLACK + Fore.GREEN + Style.BRIGHT + 'ACTIVE' + Style.NORMAL
            pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'      e-commerce site: ' + self.k8_website + "\n"
            pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'     EKS Cluster Name: ' + 'madzumo-ops-cluster' + "\n"
            pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'   EKS Cluster status: ' + self.get_cluster_status() + "\n"
            pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'        Operator Node: ' + self.ec2_instance_public_ip + "\n"
            # pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'           Prometheus: ' + self.prometheus + "\n"
            # pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'              Grafana: ' + self.prometheus + "\n"
            # pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'       Jenkins Server: ' + self.jenkins + "\n"
            # pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'                       ' + "username: admin" + "\n"
            # pipeline_info += Back.BLACK + Fore.LIGHTWHITE_EX + f'                       ' + "password: password" + "\n"

        # hc.clear_console()
        print(Back.RED + Fore.YELLOW + hc.header_art_status + Style.RESET_ALL + "\n")
        # print(Back.RED + Fore.YELLOW + header_text + "\n") # entire back is red
        print(f"{aws_conn_title} {aws_conn_status}\n{aws_conn_info}\n")
        print(f"{pipeline_title} {pipeline_status}\n{pipeline_info}")
