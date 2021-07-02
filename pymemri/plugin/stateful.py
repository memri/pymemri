# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/plugin.stateful.ipynb (unless otherwise specified).

__all__ = ['PersistentState', 'RUN_IDLE', 'RUN_INITIALIZED', 'RUN_USER_ACTION_NEEDED', 'RUN_USER_ACTION_COMPLETED',
           'RUN_STARTED', 'RUN_FAILED', 'RUN_COMPLETED', 'StatefulPlugin', 'MyStatefulPlugin']

# Cell
from ..data.schema import Item
from .pluginbase import PluginBase
import logging

# Cell
class PersistentState(Item):
    """ Persistent state variables saved for plugin such as views, accounts, the last state to resume from etc. """

    properties = Item.properties + ["pluginId", "lastState"]
    edges = Item.edges + ["account", "view"]

    def __init__(self, pluginName=None, lastState=None, account=None, view=None, **kwargs):
        super().__init__(**kwargs)
        self.pluginName = pluginName
        self.lastState = lastState
        self.account = account if account is not None else []
        self.view = view if view is not None else []

    def get_last_state(self):
        return self.lastState

    def set_last_state(self, client, state):
        self.lastState = state
        self.update(client)

    def get_account(self):
        if len(self.account) == 0:
            return None
        else:
            return self.account[0]

    def set_account(self, client, account):
        if len(self.account) == 0:
            self.add_edge('account', account)
            self.update(client)
        else:
            account_edge = self.get_edges('account')[0]
            account_edge.target = account.id
            account_edge.update(client)

    def get_view_by_name(self, view_name):
        for cvu in self.view:
            if cvu.name == view_name:
                return cvu

    def set_views(self, client, views=None):
        for view in views:
            view.update(client)
            self.add_edge('view', view)
        self.update(client)
        return True

# Cell
RUN_IDLE = 'idle'                           #1
RUN_INITIALIZED = 'initilized'              #2
RUN_USER_ACTION_NEEDED = 'userActionNeeded' # 2-3
RUN_USER_ACTION_COMPLETED = 'ready'         # 2-3
RUN_STARTED = 'start'                       #3
RUN_FAILED = 'error'                        # 3-4
RUN_COMPLETED = 'done'                      #4

logging.basicConfig(format='%(asctime)s [%(levelname)s] - %(message)s')

# Cell
class StatefulPlugin(PluginBase):
    """ Provides state/view setter and getter functions to plugin runtime """

    properties = PluginBase.properties + ["runId", "persistenceId"]
    edges = PluginBase.edges

    def __init__(self, runId=None, persistenceId=None, **kwargs):
        super().__init__(**kwargs)
        self.runId = runId
        self.persistenceId = persistenceId

    def persist(self, client, pluginName, views=None, account=None):
        persistence = PersistentState(pluginName=pluginName)
        persistence.update(client)
        self.persistenceId = persistence.id
        if views:
            persistence.set_views(client, views)
        if account:
            persistence.set_account(account)

    def get_persistence(self, client, pluginName, index=0):
        result = client.search({'type': 'PersistentState', 'pluginName': pluginName})
        if len(result) > index:
            self.persistenceId = result[index].id
            return result[index]

    def get_persistent_state(self, client):
        return client.get(self.persistenceId)

    def set_persistent_account(self, client, account):
        state = self.get_persistent_state(client)
        state.set_account(account)

    def set_persistent_last_state(self, client, lastState):
        state = self.get_persistent_state(client)
        state.set_last_state(client, lastState)

    def initialized(self, client):
        logging.warning("PLUGIN run is initialized")
        self.set_run_vars(client, {'state':RUN_INITIALIZED})

    def started(self, client):
        logging.warning("PLUGIN run is started")
        self.set_run_vars(client, {'state':RUN_STARTED})

    def failed(self, client, error):
        logging.error(f"PLUGIN run is failed: {error}")
        print("Exception while running plugin:", error)
        self.set_run_vars(client, {'state':RUN_FAILED, 'message': str(error)})

    def completed(self, client):
        logging.warning("PLUGIN run is completed")
        self.set_run_vars(client, {'state':RUN_COMPLETED})

    def complete_action(self, client):
        self.set_run_vars(client, {'state': RUN_USER_ACTION_COMPLETED})

    def action_required(self, client):
        self.set_run_vars(client, {'state': RUN_USER_ACTION_NEEDED})

    def is_action_required(self, client):
        return self.get_run_state(client) == RUN_USER_ACTION_NEEDED

    def is_action_completed(self, client):
        return self.get_run_state(client) == RUN_USER_ACTION_COMPLETED

    def is_completed(self, client):
        return self.get_run_state(client) == RUN_COMPLETED

    def is_daemon(self, client):
        run = self.get_run(client, expanded=False)
        return run.interval and run.interval > 0

    def get_run(self, client, expanded=False):
        return client.get(self.runId, expanded=expanded)

    def get_run_state(self, client):
        start_plugin = self.get_run(client)
        return start_plugin.state

    def set_run_vars(self, client, vars):
        start_plugin = client.get(self.runId, expanded=False)
        for k,v in vars.items():
            setattr(start_plugin, k, v)
        client.update_item(start_plugin)

    def get_run_view(self, client, run):
        run = self.get_run(client, expanded=True)
        if run:
            for view in run.view:
                return view

    def set_run_view(self, client, view_name):
        run = self.get_run(client)
        state = self.get_persistent_state(client)
        view = state.get_view_by_name(view_name)

        if view:

            attached_CVU_edge = self.get_run_view(client, run) # index error here if there is no already bound CVU
            if attached_CVU_edge:
                logging.warning(f"Plugin Run already has a view. Updating with {view_name}")
                attached_CVU_edge.target = view  # update CVU
                attached_CVU_edge.update(client) # having doubts if this really updates the existing edge
            else:
                logging.warning(f"Plugin Run does not have a view. Creating {view_name}")
                run.add_edge('view', view)
                run.update(client)
            return True
        return False

    def add_to_schema(self, client):
        assert client.add_to_schema(PersistentState("", ""))

# Cell
# hide
class MyStatefulPlugin(StatefulPlugin):

    def __init__(self, runId=None, **kwargs):
        super().__init__(runId=runId, **kwargs)

    def run(self):
        print("Running plugin")
        pass

    def add_to_schema(self, client):
        print("Adding schema")
        super().add_to_schema(client)
        # add plugin-specific schemas here
        pass