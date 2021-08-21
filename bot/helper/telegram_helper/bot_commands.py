from bot import START_BOT, MIRROR_BOT, UNZIP_BOT, TARMIR_BOT, CANCEL_BOT, CANCEL_ALL_BOT, LIST_BOT, STATUS_BOT
from bot import USERS_BOT, AUTH_BOT, UNAUTH_BOT, ADDSUDO_BOT, RMSUDO_BOT, RESTART_BOT, STATS_BOT, HELP_BOT
from bot import LOG_BOT, SPEEDTEST_BOT, CLONE_BOT, COUNT_BOT, YTDL_BOT, TARYTDL_BOT, DELETE_BOT
from bot import CONFIG_BOT, SHELL_BOT, UPDATE_BOT, EXEHELP_BOT, ZIP_BOT, USAGE_BOT

class _BotCommands:
    def __init__(self):
        self.StartCommand = f'{START_BOT}'
        self.MirrorCommand = f'{MIRROR_BOT}'
        self.UnzipMirrorCommand = f'{UNZIP_BOT}'
        self.TarMirrorCommand = f'{TARMIR_BOT}'
        self.ZipMirrorCommand = f'{ZIP_BOT}'
        self.CancelMirror = f'{CANCEL_BOT}'
        self.CancelAllCommand = f'{CANCEL_ALL_BOT}'
        self.ListCommand = f'{LIST_BOT}'
        self.StatusCommand = f'{STATUS_BOT}'
        self.AuthorizedUsersCommand = f'{USERS_BOT}'
        self.UsageCommand = f'{USAGE_BOT}'
        self.AuthorizeCommand = f'{AUTH_BOT}'
        self.UnAuthorizeCommand = f'{UNAUTH_BOT}'
        self.AddSudoCommand = f'{ADDSUDO_BOT}'
        self.RmSudoCommand = f'{RMSUDO_BOT}'
        self.RestartCommand = f'{RESTART_BOT}'
        self.StatsCommand = f'{STATS_BOT}'
        self.HelpCommand = f'{HELP_BOT}'
        self.LogCommand = f'{LOG_BOT}'
        self.CloneCommand = f'{CLONE_BOT}'
        self.CountCommand = f'{COUNT_BOT}'
        self.WatchCommand = f'{YTDL_BOT}'
        self.TarWatchCommand = f'{TARYTDL_BOT}'
        self.DeleteCommand = f'{DELETE_BOT}'
        self.ConfigMenuCommand = f'{CONFIG_BOT}'
        self.ShellCommand = f'{SHELL_BOT}'
        self.UpdateCommand = f'{UPDATE_BOT}'
        self.ExecHelpCommand = f'{EXEHELP_BOT}'

BotCommands = _BotCommands()
