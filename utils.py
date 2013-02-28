
from sys import stdout
from datetime import datetime


class Log(object):
    """
    Simple class log
    """

    # defining log levels and current verbosity
    def enums(**enums):
        return type('Enum', (), enums)

    log_lvl = enums(NONE=0, ERROR=1, WARNING=2, INFO=3, DEBUG=4)
    level_definition = {
        log_lvl.ERROR:'[ERROR]   ',
        log_lvl.DEBUG:'[DEBUG]   ',
        log_lvl.WARNING:'[WARNING] ',
        log_lvl.INFO:'[INFO]    ',
    }

    verbosity = log_lvl.WARNING
    log_file = stdout
    log_filename = None


    @staticmethod
    def close():
        """
        """
        if Log.log_file != stdout:
            Log.log_file.close()


    @staticmethod
    def setLogFile(log_file=None):
        """
        """
        if log_file:
            try:
                if Log.log_file != stdout:
                    Log.log_file.close()
                Log.log_file = open(log_file, 'a')
                Log.log_filename = log_file
            except IOError, e:
                Log.log_file = stdout
                Log.log(Log.log_lvl.ERROR, 'fail on opening log file ' + log_file)
        else:
            Log.log_file = stdout


    @staticmethod
    def log(verbosity, msg):
        """
        """

        if Log.verbosity >= verbosity:
            prefix = datetime.now().strftime('%Y-%m-%d %H:%m:%S ') + Log.level_definition[verbosity]
            Log.log_file.write(prefix + msg.strip().replace("\n", "\n"+' '*len(prefix)) + "\n")
            Log.log_file.flush()

