import logging

from loguru import logger

from ..data.schema import Item
from .pluginbase import PluginBase


class PersistentState(Item):
    """Persistent state variables saved for plugin such as views, accounts, the last state to resume from etc."""

    properties = Item.properties + ["pluginId", "state"]
    edges = Item.edges + ["account", "view"]

    def __init__(self, pluginName=None, state=None, account=None, view=None, **kwargs):
        super().__init__(**kwargs)
        self.pluginName = pluginName
        self.state = state
        self.account = account if account is not None else []
        self.view = view if view is not None else []

    def get_state(self):
        return self.state

    def set_state(self, client, state_str):
        self.state = state_str
        client.update_item(self)

    def get_account(self):
        if len(self.account) == 0:
            return None
        else:
            return self.account[0]

    def set_account(self, client, account):
        if len(self.account) == 0:
            if not account.id:
                client.create(account)
            self.add_edge("account", account)
            self.update(client)
        else:
            existing_account = self.account[0]
            for prop in account.properties:
                value = getattr(account, prop, None)
                if value and hasattr(existing_account, prop):
                    setattr(existing_account, prop, value)
            existing_account.update(client)

    def get_view_by_name(self, view_name):
        for cvu in self.view:
            if cvu.name == view_name:
                return cvu

    def set_views(self, client, views=None):
        for view in views:
            client.create(view)
            self.add_edge("view", view)
        self.update(client)
        return True


RUN_IDLE = "idle"  # 1
RUN_INITIALIZED = "initilized"  # 2
RUN_USER_ACTION_NEEDED = "userActionNeeded"  # 2-3
RUN_USER_ACTION_COMPLETED = "ready"  # 2-3
RUN_STARTED = "start"  # 3
RUN_FAILED = "error"  # 3-4
RUN_COMPLETED = "done"  # 4

logging.basicConfig(format="%(asctime)s [%(levelname)s] - %(message)s")


class StatefulPlugin(PluginBase):
    """Provides state/view setter and getter functions to plugin runtime"""

    properties = PluginBase.properties + ["runId", "persistenceId"]
    edges = PluginBase.edges

    def __init__(self, runId=None, persistenceId=None, **kwargs):
        super().__init__(**kwargs)
        self.runId = runId
        self.persistenceId = persistenceId

    def persist(self, client, pluginName, views=None, account=None):
        persistence = PersistentState(pluginName=pluginName)
        client.create(persistence)
        self.persistenceId = persistence.id
        if views:
            persistence.set_views(client, views)
        if account:
            persistence.set_account(account)

    def get_state(self, client, pluginName=None):
        if self.persistenceId:
            return client.get(self.persistenceId)
        elif pluginName:
            result = client.search({"type": "PersistentState", "pluginName": pluginName})
            if len(result) > 0:
                self.persistenceId = result[0].id
                return self.get_state(client)

    def set_account(self, client, account):
        state = self.get_state(client)
        state.set_account(account)

    def set_state_str(self, client, state_str):
        state = self.get_state(client)
        state.set_state(client, state_str)

    def initialized(self, client):
        logging.warning("PLUGIN run is initialized")
        self.set_run_vars(client, {"state": RUN_INITIALIZED})

    def started(self, client):
        logging.warning("PLUGIN run is started")
        self.set_run_vars(client, {"state": RUN_STARTED})

    def failed(self, client, error):
        logging.error(f"PLUGIN run is failed: {error}")
        logger.exception("Exception while running plugin:", error)
        self.set_run_vars(client, {"state": RUN_FAILED, "error": str(error)})

    def completed(self, client):
        logging.warning("PLUGIN run is completed")
        self.set_run_vars(client, {"state": RUN_COMPLETED})

    def complete_action(self, client):
        self.set_run_vars(client, {"state": RUN_USER_ACTION_COMPLETED})

    def action_required(self, client):
        self.set_run_vars(client, {"state": RUN_USER_ACTION_NEEDED})

    def is_action_required(self, client):
        return self.get_run_state(client) == RUN_USER_ACTION_NEEDED

    def is_action_completed(self, client):
        return self.get_run_state(client) == RUN_USER_ACTION_COMPLETED

    def is_completed(self, client):
        return self.get_run_state(client) == RUN_COMPLETED

    def is_failed(self, client):
        return self.get_run_state(client) == RUN_FAILED

    def is_daemon(self, client):
        run = self.get_run(client, expanded=False)
        return run.interval and run.interval > 0

    def get_run(self, client, expanded=False):
        return client.get(self.runId, expanded=expanded)

    def get_run_state(self, client):
        start_plugin = self.get_run(client)
        return start_plugin.status

    def set_run_vars(self, client, vars):
        start_plugin = client.get(self.runId, expanded=False)
        for k, v in vars.items():
            if hasattr(start_plugin, k):
                setattr(start_plugin, k, v)
        client.update_item(start_plugin)

    def get_run_view(self, client):
        run = self.get_run(client, expanded=True)
        if run:
            for view in run.view:
                return view

    def set_run_view(self, client, view_name):
        state = self.get_state(client)
        view = state.get_view_by_name(view_name)

        if view:
            attached_CVU_edge = self.get_run_view(
                client
            )  # index error here if there is no already bound CVU
            if attached_CVU_edge:
                logging.warning(f"Plugin Run already has a view. Updating with {view_name}")
                attached_CVU_edge.target = view  # update CVU
                attached_CVU_edge.update(
                    client
                )  # having doubts if this really updates the existing edge
            else:
                logging.warning(f"Plugin Run does not have a view. Creating {view_name}")
                run = self.get_run(client)
                run.add_edge("view", view)
                run.update(client)
            return True
        return False

    def add_to_schema(self, client):
        assert client.add_to_schema(PersistentState("", ""))


from ..data.schema import Person


class MyStatefulPlugin(StatefulPlugin):
    def __init__(self, runId=None, **kwargs):
        super().__init__(runId=runId, **kwargs)

    def run(self, client):
        # plugin's magic happens here

        # manipulate run state
        self.set_run_vars({"state": "Running"})

        # create items in POD
        imported_person = Person(firstName="Hari", lastName="Seldon")
        client.create(imported_person)

        # set persistent state
        self.set_state_str("continue_from:5021")

    def add_to_schema(self, client):
        logger.info("Adding schema")
        super().add_to_schema(client)
        # add plugin-specific schemas here
        client.add_to_schema(Person(firstName="", lastName=""))
        pass
