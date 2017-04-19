from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.context import InitCommandContext, ResourceCommandContext
from cloudshell.api.cloudshell_api import CloudShellAPISession
from QualiLab_CLI import Cli_Lib
from cloudshell.core.logger import qs_logger

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
        self.api_session = None
        self.logger = None
        pass

    def _log(self, context, message, level='info'):
        """

        :param ResourceCommandContext context:
        :return:
        """

        if self.logger is None:
            if hasattr(context, 'reservation'):
                self.logger = qs_logger.get_qs_logger(context.reservation.reservation_id, 'PureStorageFlashArray',
                                                  context.resource.name)
            else:
                self.logger = qs_logger.get_qs_logger('Unreserved', 'PureStorageFlashArray', context.resource.name)

        if level == 'info':
            self.logger.info(message)
        elif level == 'debug':
            self.logger.debug(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)


    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        pass


    def _write_to_output(self, message, context):

        if not self.api_session:
            self.api_session = self._get_api_session(context)

        self.api_session.WriteMessageToReservationOutput(context.reservation.reservation_id, message)

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
        self._log(context, 'connecting')
        try:
            cli_session = Cli_Lib.Cli(context.resource.address, int(context.resource.attributes['Console Port']), 'SSH',
                                      context.resource.attributes['User'],
                                      self._decrypt_password(context, context.resource.attributes['Password']),self.logger)


            cli_session.login()
            cli_session.send_and_receive('terminal length 0')



            return cli_session

        except Exception as e:

            api = self._get_api_session(context)
            api.WriteMessageToReservationOutput(context.reservation.reservation_id,
                                                '<font color=red>Error: </font>Failed to connect to ' +
                                                context.resource.name)
            api.WriteMessageToReservationOutput(context.reservation.reservation_id, 'Please check connectivity and credentials')
            raise e


    def create_zone(self, context, zone_name, vsan):
        self._log(context, 'Creating zone ' + zone_name + ' vsan ' + vsan)
        cli = self._get_cli_session(context)

        cli.send_and_receive('config t')
        cli.send_and_receive('zone name ' + zone_name + ' vsan ' + vsan)

    def get_active_zoneset_name(self, context):
        self._log(context, 'getting active zoneset')
        cli = self._get_cli_session(context)
        index, pattern, result = cli.send_and_receive('show zoneset active',pattern_list=['.*vsan.*'])

        zoneset = result.split('name')[1].split('vsan')[0].strip()
        self._log(context, 'found zoneset ' + zoneset)
        return zoneset


    def add_zone_to_zoneset(self, context, zone_name, zone_set, vsan):
        self._log(context, 'adding zone ' + zone_name + ' vsan ' + vsan + ' to zoneset ' + zone_set)
        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('zoneset name ' + zone_set + ' vsan ' +
                             vsan)
        cli.send_and_receive('member ' + zone_name)


    def add_wwn_to_zone(self, context, zone_name, vsan, wwn):
        self._log(context, 'adding wwn ' + wwn + ' to zone ' + zone_name + ' vsan ' + vsan)
        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('zone name ' + zone_name + ' vsan ' + vsan)
        cli.send_and_receive('member pwwn ' + wwn)


    def activate_zoneset(self, context, zone_set, vsan):
        self._log(context, 'activating zoneset ' + zone_set + ' vsan ' + vsan)
        cli = self._get_cli_session(context)

        result = cli.send_and_receive('config t')

        cli.send_and_receive('zoneset activate name ' + zone_set + ' vsan ' +
                             vsan, pattern_list=['.*#.*','.*ignificantly.*'])

        if result[0] == 1:
            cli.send_and_receive('y')


    def delete_zone(self, context, zone_name, vsan):
        self._log(context, 'deleting zone ' + zone_name + ' vsan ' + vsan)
        cli = self._get_cli_session(context)
        cli.send_and_receive('config t')
        cli.send_and_receive('no zone name ' + zone_name + ' vsan ' + vsan)
