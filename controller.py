import datetime
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
    def __create_options(self) -> dict:
        options = {
            "title": Option("--title", "Заголовок заметки"),
            "msg": Option("--msg", "Сообщение заметки"),
            "id": Option("--id", "Идентификатор записи"),
            "sort": Option("--sort", "Включить сортировку записей по дате создания по возрастанию", "flag"),
            "filter-before": Option("--filter-before", """Показывать только заметки созданные до даты,
            формат записи %s""" % self.date_filter_formats),
            "filter-after": Option("--filter-after", """Показывать только заметки созданные после даты,
            формат записи %s""" % self.date_filter_formats)
        }
        return options

    def __create_actions(self) -> dict:

        actions = {
            "add": Action("add", "Добавление записи", [self.options['title'], self.options['msg']], self.add),
            "delete": Action("delete", "Удаление записи", [self.options['id']], self.delete),
            "get": Action("get", "Получение записи", [self.options['id']], self.get),
            "edit": Action("edit", "Изменение записи", [self.options['id']], self.edit,
                           [self.options['title'], self.options['msg']]),
            "list": Action("list", "Получение списка записей", [], self.list,
                           [self.options['sort'], self.options['filter-before'], self.options['filter-after']]),
            "help": Action("help", "Отображение текущей страницы помощи, также может быть вызвано опциями '-h/--help'",
                           [], self.show_help)
        }
        return actions

    def __init__(self, args: list) -> None:
        self.prog_name = args[0]
        self.date_filter_formats = ['%H:%M:%S_%d-%m-%Y', '%d-%m-%Y']
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

    def delete(self) -> None:
        # TODO: maybe convert options to correct type must be done on __parse_options side
        # TODO: check if record with requested ID exist and print some warn message otherwise?
        ident = self.parsed_options['--id']
        if ident.isdigit():
            self.model.delete(int(ident))

    def edit(self) -> None:
        # TODO: maybe convert options to correct type must be done on __parse_options side
        ident = self.parsed_options['--id']
        if ident.isdigit():
            self.model.update(int(ident),
                              title=self.parsed_options['--title'] if '--title' in self.parsed_options else None,
                              msg=self.parsed_options['--msg'] if '--msg' in self.parsed_options else None
                              )

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

    @staticmethod
    def __parse_date(dt_str: str, dt_formats: list) -> datetime.datetime | None:
        for dt_format in dt_formats:
            try:
                return datetime.datetime.strptime(dt_str, dt_format)
            except ValueError:
                pass
        return None

    def list(self) -> None:
        records = self.model.get_all()
        sort = self.parsed_options['--sort'] if '--sort' in self.parsed_options else False
        before_limit = None
        if '--filter-before' in self.parsed_options:
            before_limit = self.__parse_date(self.parsed_options['--filter-before'], self.date_filter_formats)
            if before_limit is None:
                print("WARN: формат даты для '--filter-before' не распознан, параметр игнорируется")
        after_limit = None
        if '--filter-after' in self.parsed_options:
            after_limit = self.__parse_date(self.parsed_options['--filter-after'], self.date_filter_formats)
            if after_limit is None:
                print("WARN: формат даты для '--filter-after' не распознан, параметр игнорируется")
        if len(records) > 0:
            if sort:
                records = {k: v for k, v in sorted(records.items(), key=lambda item: item[1]['creation_time'])}
            for ident, record in records.items():
                show_record = True
                if show_record and before_limit is not None and record['creation_time'] >= before_limit:
                    show_record = False
                if show_record and after_limit is not None and record['creation_time'] <= after_limit:
                    show_record = False
                if show_record:
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
