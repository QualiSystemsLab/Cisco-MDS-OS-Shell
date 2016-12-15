from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context import InitCommandContext, ResourceCommandContext
from cloudshell.api.cloudshell_api import CloudShellAPISession
from QualiLab_CLI import Cli_Lib


class MdsDriver (ResourceDriverInterface):

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        pass

    def _dumblog(self, message):
        with open('c:\\temp\\dumblog.txt', 'a') as log:
            log.write(message + '\n')


    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass


    def _get_api_session(self, context):

        """

        :param ResourceCommandContext context:
        :return:
        """
        return CloudShellAPISession(context.connectivity.server_address, token_id=context.connectivity.admin_auth_token,
                                    domain=context.reservation.domain)

    def _decrypt_password(self, context, password):
        """

        :param ResourceCommandContext context:
        :return:
        """
        api = self._get_api_session(context)

        return api.DecryptPassword(password).Value

    def _get_cli_session(self, context):
        """

        :param ResourceCommandContext context:
        :return:
        """

        cli_session = Cli_Lib.Cli(context.resource.address, int(context.resource.attributes['Console Port']), 'SSH',
                                  context.resource.attributes['User'],
                                  self._decrypt_password(context, context.resource.attributes['Password']))

        self._dumblog('got session object')
        cli_session.login()
        cli_session.send_and_receive('terminal length 0')
        self._dumblog('logged in')


        return cli_session


    def create_zone(self, context, zone_name, vsan):

        cli = self._get_cli_session(context)

        cli.send_and_receive('config t')
        cli.send_and_receive('zone name ' + zone_name + ' vsan ' + vsan)

    def get_active_zoneset_name(self, context):
        cli = self._get_cli_session(context)
        index, pattern, result = cli.send_and_receive('show zoneset active',pattern_list=['.*vsan.*'])
        zoneset = result.split('name')[1].split('vsan')[0].strip
        return zoneset


    def add_zone_to_zoneset(self, context, zone_name, zone_set, vsan):
        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('zoneset name ' + zone_set + ' vsan ' +
                             vsan)
        cli.send_and_receive('member ' + zone_name)


    def add_wwn_to_zone(self, context, zone_name, vsan, wwn):

        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('zone name ' + zone_name + ' vsan ' + vsan)
        cli.send_and_receive('member pwwn ' + wwn)


    def activate_zoneset(self, context, zone_set, vsan):

        cli = self._get_cli_session(context)

        cli.send_and_receive('config t')
        cli.send_and_receive('zoneset activate name ' + zone_set + ' vsan ' +
                             vsan)


    def delete_zone(self, context, zone_name, vsan):
        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('no zone name ' + zone_name + ' vsan ' + vsan)
