from model import JsonModel


class Option:
    allowed_types: list = ['parameter', 'flag']

    def __init__(self, name: str, description: str, option_type: str = 'parameter') -> None:
        if option_type not in self.allowed_types:
            raise ValueError("option_type can by only one of %s" % self.allowed_types)
        self.name = name
        self.option_type = option_type
        self.description = description


class Action:
    def __init__(self, name: str, description, keys: list, action: callable, optional_keys: list = None) -> None:
        if optional_keys is None:
            optional_keys = []
        self.name = name
        self.description = description
        self.required_keys = keys
        self.optional_keys = optional_keys
        self.action = action


class Controller:
    @staticmethod
    def __create_options() -> dict:
        options = {
            "title": Option("--title", "Заголовок заметки"),
            "msg": Option("--msg", "Сообщение заметки"),
            "id": Option("--id", "Идентификатор записи")
        }
        return options

    def __create_actions(self) -> dict:

        actions = {
            "add": Action("add", "Добавление записи", [self.options['title'], self.options['msg']], self.add),
            "get": Action("get", "Получение записи", [self.options['id']], self.get),
            "list": Action("list", "Получение списка записей", [], self.list),
            "help": Action("help", "Отображение текущей страницы помощи, также может быть вызвано опциями '-h/--help'",
                           [], self.show_help)
        }
        return actions

    def __init__(self, args: list) -> None:
        self.prog_name = args[0]
        self.options = self.__create_options()
        self.actions = self.__create_actions()
        self.action = None
        self.parsed_options = {}
        self.argparse_success = False
        self.argparse_msg = ""
        self.parse_arguments(args[1:])
        self.prog_info = "Приложение заметки (python) Консольная версия"
        self.prog_usage = "usage: %s ACTION [OPTIONS]" % self.prog_name
        self.model = JsonModel()

    def add(self) -> None:
        self.model.add(title=self.parsed_options['--title'], msg=self.parsed_options['--msg'])

    @staticmethod
    def __fancy_record_print(ident: int | str, record: dict) -> None:
        print("-" * 6)
        print("id: %s" % ident)
        # TODO: datetime.strftime(more_human_readable_format)?
        print("created: %s" % record['creation_time'].isoformat())
        print("changed: %s" % record['modification_time'].isoformat())
        print("header: %s" % record['title'])
        print("body: %s" % record['msg'])
        print("-" * 6)

    def get(self) -> None:
        # TODO: maybe convert options to correct type must be done on __parse_options side
        record = None
        ident = self.parsed_options['--id']
        if ident.isdigit():
            record = self.model.get(int(ident))
        if record:
            self.__fancy_record_print(ident, record)
        else:
            print("No Data")

    def list(self) -> None:
        records = self.model.get_all()
        if len(records) > 0:
            for ident, record in records.items():
                self.__fancy_record_print(ident, record)
        else:
            print("No Data")

    def show_help(self) -> None:
        print(self.prog_info)
        print(self.prog_usage)
        print("Доступные действия: %s" % list(self.actions.keys()))
        print()
        print("Описания действий")
        for _, action in self.actions.items():
            print('  %s: %s' % (action.name, action.description))
            if len(action.required_keys) > 0:
                print("  Обязательные опции")
                for option in action.required_keys:
                    print("    %s: %s" % (option.name, option.description))
            if len(action.optional_keys) > 0:
                print("  Дополнительные опции")
                for option in action.optional_keys:
                    print("    %s: %s" % (option.name, option.description))
            print()

    def parse_arguments(self, args: list) -> None:
        if len(args) == 0:
            self.action = self.actions["help"]
            self.argparse_success = False
            return
        # catch -h/--help request
        if '-h' in args or '--help' in args:
            self.action = self.actions["help"]
            self.argparse_success = True
            return
        # get action from args
        action = args[0]
        possible_actions = list(self.actions.keys())
        if action not in possible_actions:
            self.argparse_msg = "Incorrect action '%s', please choose one of %s" % (action, possible_actions)
            self.action = self.actions["help"]
            self.argparse_success = False
            return
        self.action = self.actions[action]
        self.argparse_success = True
        # get options from args
        self.__parse_options(args[1:])

    def __parse_options(self, args: list) -> None:
        options_map = {val.name: val for key, val in self.options.items()}
        self.parsed_options = {option.name: None if option.option_type == "parameter" else False
                               for option in self.action.required_keys}
        i = 0
        while i < len(args):
            option = args[i]
            if option in options_map.keys():
                if options_map[option].option_type == "parameter":
                    i += 1
                    if i < len(args):
                        option_val = args[i]
                    else:
                        option_val = None
                        print("WARN: parameter for option '%s' not set" % option)
                else:
                    option_val = True
                if options_map[option] not in self.action.required_keys and \
                        options_map[option] not in self.action.optional_keys:
                    print("WARN: option '%s' has no effect on action '%s' and will be ignored" %
                          (option, self.action.name))
                self.parsed_options[option] = option_val
            else:
                print("WARN: unknown option '%s', ignored" % option)
            i += 1
        # validate parameters (check not empty for now)
        empty_parameters = [key for key, val in self.parsed_options.items() if val is None]
        if len(empty_parameters) > 0:
            self.argparse_success = False
            self.argparse_msg = "Not enough options for action '%s', you also need to set %s" % \
                                (self.action.name, empty_parameters)

    def start(self) -> None:
        if self.argparse_success:
            self.action.action()
        else:
            if len(self.argparse_msg) > 0:
                print(self.argparse_msg)
            self.show_help()


if __name__ == '__main__':
    print("This is internal class, do not run this")
    exit(1)
